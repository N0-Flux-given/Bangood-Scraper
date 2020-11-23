import urllib3
import httplib2
import re
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen as ureq
from urllib.parse import quote

import sqlite3

import pandas as pd
import tkinter as tk

import time
import threading


class Scraper:

    def __init__(self, product_name, gui):
        self.lis_headers = ["Name", "Price", "Old Price", "Percent off", "Reviews",
                            "Rating Total", "5 stars", "4 stars", "3 stars", "2 Stars", "1 Star"]
        # lis_headers = ["Name", "Price", "Old Price", "Percent off", "Reviews"]
        #                  0         1       2             3             4            5            6          7           8          9         10
        self.lis_data = [list() for i in range(len(self.lis_headers))]
        self.pages = 0
        self.sql_buffer = []
        self.count = 0
        self.product_name = product_name.replace(" ", "-")

        self.connection = sqlite3.connect(f"{self.product_name}.db")
        self.cursor = self.connection.cursor()
        self.csv = False
        self.gui = gui

        self.commit_at = 20
        print(len(self.lis_data))
        print(len(self.lis_headers))

    def transaction(self, sql):
        self.sql_buffer.append(sql)  # DOUBT!!!!
        if len(self.sql_buffer) >= self.commit_at:
            print("Starting transaction!")
            self.cursor.execute("BEGIN TRANSACTION")
            for query in self.sql_buffer:
                try:
                    self.cursor.execute(query)
                except Exception as e:
                    print(e)
            self.connection.commit()
            print("Commit successful!")
            self.sql_buffer = []

    def create_table(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS product_table(prod_name VARCHAR(500), price FLOAT, old_price FLOAT, "
            "percent_off INT(3), reviews INT(6), rating_total FLOAT, stars_5 INT(5), stars_4 INT(5), stars_3 INT(5), "
            "stars_2 INT(5), stars_1 INT(5))")

    def get_page_soup(self, url):
        uclient = ureq(httplib2.iri2uri(url))
        page_html = uclient.read()
        uclient.close()
        return BeautifulSoup(page_html, "html")

    def scrape(self, page_soup):
        cards = page_soup.find_all("div", class_="p-wrap")

        for card in cards:
            print("Card: ", cards.index(card))
            try:  # Try to get the Name and reviews of the product
                a = card.find_all("a")
                try:
                    self.lis_data[0].append(a[1].text)  # Name
                except Exception as e:
                    self.lis_data[0].append("NaN")  # write nan if not found
                try:
                    self.lis_data[4].append(int(a[2].text[:-8]))  # review
                except Exception as e:
                    self.lis_data[4].append("NaN")
            except Exception as e:
                self.lis_data[0].append("NaN")  # 'Nan' for both name and review if finding the 'a' tag fails
                self.lis_data[4].append("NaN")
            try:  # Try to find price
                price = card.find("span", class_="price-box")
                pattern = re.compile(r"\n+(.*?)\n")
                matches = pattern.findall(price.text)
                price = matches[0][1:].split(",")
                price_final = ""
                for i in price:
                    price_final += i
                self.lis_data[1].append(float(price_final))
            except Exception as e:
                self.lis_data[1].append("NaN")
            try:
                price_old = card.find("span", class_="price-old-box")
                spans = price_old.find_all("span")
                try:
                    price = spans[0].text[1:].split(",")
                    price_final = ""
                    for i in price:
                        price_final += i
                    self.lis_data[2].append(float(price_final))  # Old Price ---- spans[0].text
                except Exception as e:
                    self.lis_data[2].append("NaN")
                try:
                    self.lis_data[3].append(int(spans[1].text[:-5]))  # % off ----- spans[1].text
                except Exception as e:
                    self.lis_data[3].append("NaN")
            except Exception as e:
                self.lis_data[2].append("NaN")
                self.lis_data[3].append("NaN")
            self.scrape_stars(card)
            if not self.csv:
                def check_null(x): return "NULL" if x == "NaN" else x

                query = f"INSERT INTO product_table (prod_name, price, old_price, percent_off, reviews, rating_total, stars_5, stars_4, stars_3, stars_2, stars_1) VALUES ('{check_null(self.lis_data[0][self.count])}', {check_null(self.lis_data[1][self.count])}, {check_null(self.lis_data[2][self.count])}, {check_null(self.lis_data[3][self.count])}, {check_null(self.lis_data[4][self.count])}, {check_null(self.lis_data[5][self.count])}, {check_null(self.lis_data[6][self.count])}, {check_null(self.lis_data[7][self.count])}, {check_null(self.lis_data[8][self.count])}, {check_null(self.lis_data[9][self.count])}, {check_null(self.lis_data[10][self.count])})"
                self.transaction(query)
                print(query)
            self.count += 1
            # break

    def scrape_stars(self, card):
        review_link = card.find("a", class_="review", href=True)
        # print(review_link['href'])
        stars_soup = self.get_page_soup(review_link['href'])
        rev_score = stars_soup.find("div", class_="rev-score")
        try:
            self.lis_data[5].append(float(rev_score.find("div", class_="score").text[:-9]))
        except Exception as e:
            self.lis_data[5].append("NaN")
        try:
            stars = stars_soup.find_all("a", class_="star")
            try:
                star = stars[0].find("span", class_="histogram-count").text
                self.lis_data[6].append(int(star.split(" ")[0]))  # 5 star
            except Exception as e:
                self.lis_data[6].append("NaN")
            try:
                star = stars[1].find("span", class_="histogram-count").text
                self.lis_data[7].append(int(star.split(" ")[0]))  # 4 star
            except Exception as e:
                self.lis_data[7].append("NaN")
            try:
                star = stars[2].find("span", class_="histogram-count").text
                self.lis_data[8].append(int(star.split(" ")[0]))  # 3 star
            except Exception as e:
                self.lis_data[8].append("NaN")
            try:
                star = stars[3].find("span", class_="histogram-count").text
                self.lis_data[9].append(int(star.split(" ")[0]))  # 2 star
            except Exception as e:
                self.lis_data[9].append("NaN")
            try:
                star = stars[4].find("span", class_="histogram-count").text
                self.lis_data[10].append(int(star.split(" ")[0]))  # 1 star
            except Exception as e:
                self.lis_data[10].append("NaN")
        except Exception as e:
            for i in range(6, 11):
                self.lis_data[i].append("NaN")

    def init_scrape(self):
        current_page = 1

        url = f"https://www.banggood.in/search/{self.product_name}/0-0-0-1-1-60-0-price-0-0_p-{current_page}.html"
        total_pages = self.get_page_soup(url).find("div", class_="total")
        pages = total_pages.text
        self.pages = int(pages[6:8])  # Make a log here
        self.gui.log(f"Found {self.pages} pages for {self.product_name}")

    def start_scraping(self, csv, pages):
        if csv:
            self.csv = True
            for page in range(1, int(pages)+1):
                url = f"https://www.banggood.in/search/{self.product_name}/0-0-0-1-1-60-0-price-0-0_p-{page}.html"
                # print(url)
                self.scrape(self.get_page_soup(url))
                self.gui.log(f"Page {page} done")
            m_dic = {"Name": self.lis_data[0], "Price": self.lis_data[1], "Old Price": self.lis_data[2],
                     "Percent Off": self.lis_data[3], "reviews": self.lis_data[4], "Rating Total": self.lis_data[5],
                     "5 stars": self.lis_data[6], "4 stars": self.lis_data[7], "3 stars": self.lis_data[8],
                     "2 stars": self.lis_data[9],
                     "1 star": self.lis_data[10]}
            df = pd.DataFrame(m_dic)
            df.to_csv(f"{self.product_name}.csv")
            self.gui.log("Scraping complete!")
            self.gui.log(f"Check {self.product_name}.csv for results")
            # self.connection.close()
        else:
            self.csv = False
            for page in range(1, pages):
                url = f"https://www.banggood.in/search/{self.product_name}/0-0-0-1-1-60-0-price-0-0_p-{page}.html"
                self.gui.log(f"Page {page} done")
                # print(url)
                self.scrape(self.get_page_soup(url))
            self.gui.log("Scraping complete!")
            self.gui.log(f"Check current directory for results")


class GUI:
    def __init__(self):
        self.window = tk.Tk()
        self.log_texts = []
        self.logs = []
        self.scraper = None
        self.csv = True

        for i in range(5):
            self.log_texts.append(tk.StringVar(self.window))
            self.log_texts[i].set("")

        for i in range(5):
            self.logs.append(tk.Label(self.window, textvariable=self.log_texts[i]))

        self.window.geometry("450x500")
        self.window.title("Bangood Scraper")

        self.txt = tk.Entry(self.window, width=50)
        self.txtLabel = tk.Label(self.window, text="Enter product name")
        self.btnSet = tk.Button(self.window, text="OK", padx=50, command=self.onOkClick)
        self.txtLabel.grid(column=0, row=0)
        self.txt.grid(column=0, row=1, sticky="e")
        self.btnSet.grid(column=1, row=1)
        self.radio_var = tk.IntVar()
        self.r1 = tk.Radiobutton(self.window, text="CSV", variable=self.radio_var, value=1, command=self.onRadioChange)
        self.r1.select()
        self.r2 = tk.Radiobutton(self.window, text="sqlite3 database", variable=self.radio_var, value=2,
                                 command=self.onRadioChange)
        self.r1.grid(column=0, row=2)
        self.r2.grid(column=1, row=2)

        self.pages_till_scrape_var = tk.IntVar()

        self.pages_to_scrape = tk.Entry(self.window, width=50)
        # self.pages_to_scrape.insert(0, "Enter comma separated numbers")
        # self.pages_to_scrape_radio = tk.Radiobutton(self.window, text="Scrape these pages", variable=self.pages_till_scrape_var, value=1, command=self.onPageRangeRadioClick) # 1-> comma separated list

        self.pages_till = tk.Entry(self.window, width=50)
        self.pages_till.insert(0, "Enter page number to scrape till")
        self.pages_to_scrape_radio2 = tk.Radiobutton(self.window, text="Scrape till this page", variable=self.pages_till_scrape_var, value=2, command=self.onPageRangeRadioClick) # 2-> till
        self.pages_to_scrape_radio3 = tk.Radiobutton(self.window, text="Scrape All pages",
                                                     variable=self.pages_till_scrape_var, value=3, command=self.onPageRangeRadioClick) # 3 ->  All
        self.pages_to_scrape_radio3.select()
        self.btnStart = tk.Button(self.window, text="Start!", padx=50, command=self.onStartClick)

        self.pages_till["state"] = "disabled"
        self.pages_to_scrape["state"] = "disabled"
        self.pages_to_scrape_radio3["state"] = "disabled"
        self.pages_to_scrape_radio2["state"] = "disabled"
        # self.pages_to_scrape_radio["state"] = "disabled"
        self.btnStart["state"] = "disabled"


        self.pages_to_scrape_radio3.grid(column=0, row=3)
        # self.pages_to_scrape.grid(column=0, row=4)
        # self.pages_to_scrape_radio.grid(column=1, row=4)
        self.pages_till.grid(column=0, row=5)
        self.pages_to_scrape_radio2.grid(column=1, row=5)
        self.btnStart.grid(column=0, row=6)




        self.log_start_row = 7
        for log in self.logs:
            log.grid(column=0, row=self.log_start_row)
            self.log_start_row += 1

        # label = tk.Label(window, text="It worked").pack()
        self.window.mainloop()

    def onStartClick(self):
        self.btnStart["state"] = "disabled"
        self.log("Starting to scrape...")
        print(type(self.pages_till_scrape_var.get()))
        if self.pages_till_scrape_var.get() == 3: # All pages
            print("Starting scrape thread with all pages")
            scrape_thread = threading.Thread(target=self.scrapeAsync, args=(self.scraper.pages,)) # All pages
            scrape_thread.start()
        else:
            print("Starting scrape thread till given page")
            scrape_thread = threading.Thread(target=self.scrapeAsync, args=(self.pages_till.get(),))
            scrape_thread.start()



    def initialize_stage2_controls(self):
        self.btnStart["state"] = "normal"
        # self.pages_to_scrape_radio["state"] = "normal"
        self.pages_to_scrape_radio2["state"] = "normal"
        self.pages_to_scrape_radio3["state"] = "normal"


    def onPageRangeRadioClick(self):
        if self.pages_till_scrape_var.get() == 3:
            self.pages_till["state"] = "disabled"
            self.pages_to_scrape["state"] = "disabled"
        if self.pages_till_scrape_var.get() == 2:
            self.pages_till["state"] = "normal"
            self.pages_to_scrape["state"] = "disabled"
        if self.pages_till_scrape_var.get() == 1:
            self.pages_till["state"] = "disabled"
            self.pages_to_scrape["state"] = "normal"

    def onRadioChange(self):
        if self.radio_var.get() == 1:
            self.csv = True
        else:
            self.csv = False

    def onOkClick(self):
        init_thread = threading.Thread(target=self.okAsync)
        init_thread.start()

    def scrapeAsync(self, pages): # Runs in a separate thread
        # print(pages)
        # print(type(pages))
        print("In scraping thread, pages:", pages)
        self.scraper.start_scraping(self.csv, pages)

    def okAsync(self):
        if self.txt.get() == "":
            self.log("Enter something...")
        else:
            prod_name = self.txt.get().replace(" ", "-")  # replace spaces with hyphens for the url
            self.log(f"Looking up '{self.txt.get()}' on bangood...")
            self.btnSet["state"] = "disabled"
            self.r1["state"] = "disabled"
            self.r2["state"] = "disabled"
            self.scraper = Scraper(product_name=self.txt.get(), gui=self)
            self.scraper.init_scrape()
            self.initialize_stage2_controls()

    def log(self, text):
        for i in range(len(self.logs) - 1, -1, -1):
            self.log_texts[i].set(self.log_texts[i - 1].get())
        self.log_texts[0].set(text)


mgui = GUI()
