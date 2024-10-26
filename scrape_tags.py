import os
import asyncio
import aiohttp
import collections
import csv
import time
import multiprocessing
from tqdm import tqdm
from rich.console import Console
from rich.progress import track

console = Console()

csv_filename = input('Output filename: ')
minimum_count = input('Minimum tag count (> 50 is preferable): ')
dashes = input("replace '_' with '-'? (often better for prompt following) (y/N): ")
exclude = input('enter categories to exclude: (general,artist,copyright,character,post) (press enter for none): \n')
alias = input('Include aliases? (Only supported in tag-complete) (y/N): ')

excluded = ""
excluded += "0" if "general" in exclude else ""
excluded += "1" if "artist" in exclude else ""
excluded += "3" if "copyright" in exclude else ""
excluded += "4" if "character" in exclude else ""
excluded += "5" if "post" in exclude else ""

kaomojis = [
    "0_0", "(o)_(o)", "+_+", "+_-", "._.", "<o>_<o>", "<|>_<|>", "=_=", ">_<",
    "3_3", "6_9", ">_o", "@_@", "^_^", "o_o", "u_u", "x_x", "|_|", "||_||",
]

if not '.csv' in csv_filename:
    csv_filename += '.csv'

if 'y' in dashes.lower():
    dashes = 'y'
    csv_filename += '-temp'
else:
    dashes = 'n'

if not 'y' in alias.lower():
    alias = 'n'

if not minimum_count.isdigit():
    minimum_count = 50
else:
    minimum_count = int(minimum_count)

# Base URLs
base_url = 'https://danbooru.donmai.us/tags.json?limit=1000&search[hide_empty]=yes&search[is_deprecated]=no&search[order]=count'
alias_url = 'https://danbooru.donmai.us/tag_aliases.json?commit=Search&limit=1000&search[order]=tag_count'

aliases = collections.defaultdict(str)

# Determine the number of worker threads based on CPU cores
num_workers = multiprocessing.cpu_count()

async def fetch_json(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            console.print(f"[red]Failed to fetch data from {url}. HTTP Status Code: {response.status}[/red]")
            return None

async def fetch_aliases():
    global aliases
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, 1001):
            url = f'{alias_url}&page={page}'
            tasks.append(fetch_json(session, url))

        # Execute tasks concurrently and show progress bar with tqdm
        for data in tqdm(await asyncio.gather(*tasks), desc="Fetching Aliases", unit="page"):
            if not data:
                continue
            for item in data:
                if aliases[item['consequent_name']]:
                    aliases[item['consequent_name']] += ',' + item['antecedent_name']
                else:
                    aliases[item['consequent_name']] = item['antecedent_name']
        console.print("[green]All alias pages processed.[/green]")

async def process_page(session, page, data_list):
    url = f'{base_url}&page={page}'
    data = await fetch_json(session, url)
    if not data:
        console.print(f"[yellow]No more tag data found at page {page}. Stopping.[/yellow]")
        return False  # Signal to stop fetching
    for item in data:
        if int(item['post_count']) < minimum_count:
            return False  # Signal to stop fetching
        if str(item['category']) not in excluded:
            if alias == 'n':
                data_list.append([item['name'], item['category'], int(item['post_count']), ''])
            else:
                alt = aliases.get(item['name'], '')
                data_list.append([item['name'], item['category'], int(item['post_count']), alt])
    return True  # Signal to continue fetching

async def fetch_tags():
    data_list = []
    total_pages = 1000
    async with aiohttp.ClientSession() as session:
        with tqdm(total=total_pages, desc="Fetching Tags", unit="page") as pbar:
            page = 1
            continue_fetching = True
            while continue_fetching and page <= total_pages:
                tasks = []
                for _ in range(num_workers):
                    tasks.append(process_page(session, page, data_list))
                    page += 1
                # Run the tasks concurrently
                results = await asyncio.gather(*tasks)
                # Update progress bar
                pbar.update(len(tasks))
                # Check if any task returned False (indicating to stop)
                if not all(results):
                    console.print(f"[yellow]All tags with {minimum_count} posts or greater have been scraped.[/yellow]")
                    continue_fetching = False
                    break

    # After all data is collected, sort by post_count
    console.print('[blue]Sorting data by post_count...[/blue]')
    sorted_data_list = sorted(data_list, key=lambda x: x[2], reverse=True)

    # Write sorted data to the file using rich progress bar
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in track(sorted_data_list, description="Writing to CSV"):
            writer.writerow(row)

async def replace_dashes():
    if dashes == 'y':
        console.print("[blue]Replacing '_' with '-'[/blue]")
        with open(csv_filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            with open(csv_filename.replace('-temp', ''), 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile)
                for row in track(reader, description="Processing Dashes"):
                    if row and row[0] not in kaomojis:
                        row[0] = row[0].replace("_", "-")
                        if len(row) > 3:
                            row[3] = row[3].replace("_", "-")
                    writer.writerow(row)
        os.remove(csv_filename)

async def main():
    if alias == 'y':
        await fetch_aliases()
    await fetch_tags()
    await replace_dashes()
    console.print(f"[green]Data has been written to {csv_filename.replace('-temp', '')}[/green]")

if __name__ == "__main__":
    asyncio.run(main())
