import os
import requests
import csv
import time

csv_filename = input('Output filename: ')
minimum_count = input('Minimum tag count (> 50 is preferable): ')
dashes = input('replace \'_\' with \'-\'? (often better for prompt following) (Y/n): ')
exclude = input('enter categories to exclude: (general,artist,copyright,character,post) (press enter for none): \n')

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

if dashes.lower != 'n':
    print()
    dashes = 'y'
    csv_filename += '-temp'

if not minimum_count.isdigit():
    minimum_count = 50

# Base URL without the page parameter
base_url = 'https://danbooru.donmai.us/tags.json?limit=1000&search[hide_empty]=yes&search[is_deprecated]=no&search[order]=count'

# Open a file to write
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Loop through pages 1 to 1000
    class Complete(Exception): pass
    try:
        for page in range(1, 1001):
            # Update the URL with the current page
            url = f'{base_url}&page={page}'

            # Fetch the JSON data
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()

                # Break the loop if the data is empty (no more tags to fetch)
                if not data:
                    print(f'No more data found at page {page}. Stopping.', flush=True)
                    break
                
                # Write the data
                for item in data:
                    if int(item['post_count']) < int(minimum_count): # break if below minimum count
                        file.flush()
                        raise Complete
                    if not str(item['category']) in excluded:
                        writer.writerow([item['name'],item['category'],item['post_count'],''])

                # Explicitly flush the data to the file
                file.flush()
            else:
                print(f'Failed to fetch data for page {page}. HTTP Status Code: {response.status_code}', flush=True)
                break

            print(f'Page {page} processed.', flush=True)
            # Sleep for 0.5 second because we have places to be
            time.sleep(0.5)
    except Complete:
        print(f'All tags with {minimum_count} posts or greater have been scraped.')
    file.close()

    if dashes == 'y':
        print(f'Replacing \'_\' with \'-\'')
        with open(csv_filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            with open(csv_filename.removesuffix('-temp'), 'w', newline='') as outfile:
                writer = csv.writer(outfile)
                for row in reader:
                    if not row[0] in kaomojis:
                        row[0] = row[0].replace("_", "-")
                    writer.writerow(row)
                outfile.close()    
            csvfile.close()
        os.remove(csv_filename)
        csv_filename = csv_filename.removesuffix('-temp')

print(f'Data has been written to {csv_filename}', flush=True)