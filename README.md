# Bangood-Scraper
A scraping tool to extract information from bangood. Just download and run the 'scrape_bangood.py' script.

## The UI:
![alt text](https://i.imgur.com/69vXoWI.png)

 Enter the product name you want to scrape info for in the text box, then click either of the radio buttons to have output as a .csv file or as a sqlite3 database.
 For the database, NaN values are entered into the table as NULL.
 
 After you hit OK, the script will make contact with bangood.com for the given search term. It will display the number of pages it found. 
 Then choose if you want to scrape all the pages or only upto a specific page number. 
 Make sure the number you enter is less than the total pages!
 
 Press 'Scrape' and wait for it to go through all the pages and generate a nice table.
 

## The results:
 ![alt text](https://i.imgur.com/ZrJCUpI.png)

This is the table you'll get after loking up for a product.
