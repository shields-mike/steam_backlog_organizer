import bs4
import csv
import requests
import re
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class Steam:
    def __init__(self, driver):
        """Declare values needed for the class.

        Args:
            driver (class): Firefox webdriver
        """
        self.driver = driver

        # Replace with your own profile link
        user_url = "https://steamcommunity.com/id/FractalNoise/games/?tab=all"
        self.driver.get(user_url)
        print("Acquiring url data...")

        self.soup = bs4.BeautifulSoup(self.driver.page_source, "lxml")

    def game_count(self):
        """Counts how many games are in your library.

        Returns:
            int: Number of games in your library
        """
        return len(self.soup.find_all("div", class_="gameListRowItemName ellipsis"))

    def page_number(self):
        """Finds the specific set of numbers used to find the store page of the game.

        Returns:
            str: Game page id
        """
        return (
            page_id["id"].split("_")[1]
            for page_id in self.soup.find_all("div", class_="gameListRow")
        )

    def hours_played(self):
        """Generator object that returns the number of hours played.

        Returns:
            str: Number of hours played
        """
        return (
            hours.text
            for hours in self.soup.find_all("h5", class_="ellipsis hours_played")
        )


class Games:
    def __init__(self, next_page, game_hours, write_header_count):
        """Declare values needed for the class.

        Args:
            next_page (str): Game page id
            game_hours (str): Number of hours played
            write_header_count (int): A count of how many times the header has been written
        """
        self.game_dict = {}
        self.write_header_count = write_header_count
        self.next_page = next_page
        self.game_dict["Hours Played"] = game_hours

        # Acquire the game page html
        req = requests.get(f"https://store.steampowered.com/app/{self.next_page}")
        self.page_soup = bs4.BeautifulSoup(req.text, "lxml")

    def game_name(self):
        """Grabs the title of the game."""
        title = self.page_soup.find("div", class_="apphub_AppName")

        # Checks if the game title exists on the page
        if title is not None:
            self.game_dict["Game Title"] = title.text

    def description(self):
        """Grabs the description of the game."""
        desc = self.page_soup.find("div", class_="game_description_snippet")

        # Checks if the game description exists on the page
        if desc is not None:
            self.game_dict["Description"] = desc.text.strip()

    def release_date(self):
        """Grabs the release date of the game."""
        date = self.page_soup.find("div", class_="date")

        # Checks if the release date exists on the page
        if date is not None:
            self.game_dict["Release Date"] = date.text

    def recent_reviews(self):
        """Grabs the recent reviews section of the game."""
        recent = self.page_soup.find("div", class_="summary column")

        # Checks if recent reviews exists on the page
        if recent is not None:
            self.game_dict["Recent Reviews"] = " ".join(recent.text.split())

    def all_reviews(self):
        """Grabs the all reviews section of the game."""
        all_time = self.page_soup.find("div", class_="summary column")

        # Checks if all reviews exists on the page
        if all_time is not None:
            self.game_dict["All Reviews"] = " ".join(
                all_time.find_next("div", class_="summary column").text.split()
            )

    def tags(self):
        """Grabs the game tags."""
        tags_list = self.page_soup.find_all("a", class_="app_tag", limit=5)

        # Checks if game tags exist on the page
        if tags_list is not None:
            self.game_dict["Tags"] = ", ".join([tag.text.strip() for tag in tags_list])

    def write(self):
        """Opens and writes the data to the csv file."""
        with open("steam_backlog.csv", "a", newline="", encoding="utf-8") as steam_file:
            fieldnames = [
                "Game Title",
                "Description",
                "Hours Played",
                "Release Date",
                "Recent Reviews",
                "All Reviews",
                "Tags",
            ]

            csv_writer = csv.DictWriter(steam_file, fieldnames=fieldnames)

            # Checks if the header row has already been written
            if self.write_header_count == 0:
                csv_writer.writeheader()

            csv_writer.writerow(self.game_dict)

            # Checks if there is a game being written to the file
            if "Game Title" in self.game_dict:
                print(f"Writing {self.game_dict['Game Title']} to file")


def main():
    write_header_count = 0
    print("Initializing webdriver...")

    # Make the webdriver run in headless mode
    options = Options()
    options.headless = True

    # Replace the executable path with the path to your webdriver download
    driver = webdriver.Firefox(
        options=options, executable_path=r"G:\Downloads v2\geckodriver.exe"
    )

    # Make a new profile object
    profile = Steam(driver)

    # Grab info from the initial page
    number_of_games = profile.game_count()
    page_num_gen = profile.page_number()
    hours_gen = profile.hours_played()

    # Keep looping for every game in the users library
    for _ in range(number_of_games):
        # Advance the generator
        next_page = next(page_num_gen)
        game_hours = next(hours_gen)

        # Make a new game object
        game = Games(next_page, game_hours, write_header_count)

        # Grab all the info from the game page
        game.game_name()
        game.description()
        game.release_date()
        game.recent_reviews()
        game.all_reviews()
        game.tags()

        # Write to the file
        game.write()
        write_header_count += 1

        # Wait two seconds so the server doesn't get bombarded with requests
        time.sleep(2)

    print("Process complete")
    # Exit the firefox webdriver
    driver.quit()


if __name__ == "__main__":
    main()

