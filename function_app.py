import datetime
import pytz
import xml.etree.cElementTree as ET
import argparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions

timezone = pytz.UTC

# TODO: Add possibility to load name mapping from file
channels_name_mapping = {}

channels_by_name = {}
save_path = "./guide.xmltv"
days = 3

parser = argparse.ArgumentParser("bein-guide")
parser.add_argument("save_path", help="Relative or absolute path to output the xmltv file.", type=str)
parser.add_argument("days", help="Number of days to grab starting from today.", type=str, default=days)
args = parser.parse_args()

options = FirefoxOptions()
options.log.level = "trace"
options.add_argument("-devtools")
driver = webdriver.Remote("http://localhost:4444", options=options)


class Channel:
    def __init__(self, name, img):
        self.name = name
        self.img = img
        self.programs = []

    def get_formatted_name(self):
        if self.name in channels_name_mapping:
            return channels_name_mapping[self.name]

        return self.name


class TimeInterval:
    def __init__(self, date, start_hour, start_minute, end_hour, end_minute):
        self.date = date
        self.end_minute = int(end_minute)
        self.end_hour = int(end_hour)
        self.start_minute = int(start_minute)
        self.start_hour = int(start_hour)

    def day_overlap(self):
        return self.start_hour > self.end_hour

    def get_start_datetime(self):
        start_time = datetime.time(self.start_hour, self.start_minute, tzinfo=timezone)
        return datetime.datetime.combine(self.date, start_time)

    def get_end_datetime(self):
        end_date = self.date
        if self.day_overlap():
            end_date = self.date + datetime.timedelta(days=1)
        start_time = datetime.time(self.end_hour, self.end_minute, tzinfo=timezone)
        return datetime.datetime.combine(end_date, start_time)


class Program:
    def __init__(self, title: str, desc: str, timer: TimeInterval):
        self.title = title
        self.desc = desc
        self.timer = timer


def process_channel(div, date):
    global channels_by_name

    print("  Processing {}".format(div.get_attribute("id")))

    img = div.find_element(By.XPATH, "./div[1]/div/div/div/a/img")
    name, img_url = process_name(img)
    if name in channels_by_name:
        print("    Existing channel: {}".format(name))
        channel = channels_by_name[name]
    else:
        print("    New channel: {}".format(name))
        channel = Channel(name, img_url)
        channels_by_name[name] = channel

    program_lis = div.find_elements(By.XPATH, "./div[2]/div/ul/li")[3:]
    programs = []
    reject_overlap = True
    for li in program_lis:
        program = create_program(li, date)
        if reject_overlap and program.timer.day_overlap():
            continue

        reject_overlap = False
        programs.append(program)

    channel.programs += programs
    print("    Found {} new programs".format(len(programs)))

    return channel


def process_name(img):
    img_url = img.get_attribute("src")
    name = img_url.split("/")[-1][:-3]
    return name, img_url


def create_program(li, date):
    timer_div = li.find_element(By.XPATH, "./div[2]/p")
    timer_text = timer_div.text.strip()
    [[start_hour, start_min], [end_hour, end_min]] = [t.split(":") for t in timer_text.split(" - ")]
    timer = TimeInterval(date, start_hour, start_min, end_hour, end_min)

    data_div = li.find_elements(By.XPATH, "./div[1]/p")
    title = data_div[0].text
    desc = data_div[1].text

    return Program(title, desc, timer)


def process_day(date):
    print("Getting channels for {}".format(date.strftime("%y/%m/%d")))

    # offset=-3 to use UTC time
    url = ("https://www.bein.com/ar/epg-ajax-template/"
           "?action=epg_fetch"
           "&offset=-3"
           "&category=sports"
           "&serviceidentity=bein.net"
           "&mins=00"
           "&cdate={year}-{month}-{day}"
           "&language=AR"
           "&postid=25344"
           "&loadindex=0").format(year=date.year, month=date.month, day=date.day)

    driver.get(url)

    try:
        channel_1 = driver.find_element(By.ID, 'channels_1')
    except NoSuchElementException:
        print("No channel found")
        return []

    channel_divs = channel_1.find_elements(By.XPATH, './../div[starts-with(@id, "channels_")]')
    [process_channel(div, date) for div in channel_divs]


def format_datetime_to_xmltv(dt: datetime.datetime):
    return dt.strftime("%Y%m%d%H%M%S +0000")


def build_xml():
    print("Building XMLTV file")
    xtv = ET.Element("tv")
    xtv.set("generator-info-name", "Personal BeIN gen")
    xtv.set("generator-info-url", "https://hathoute.com")

    for c in channels_by_name.values():
        xchannel = ET.SubElement(xtv, "channel")
        xchannel.set("id", c.name)
        ET.SubElement(xchannel, "display-name").text = c.get_formatted_name()
        ET.SubElement(xchannel, "icon", src=c.img)
        for p in c.programs:
            xprogramme = ET.SubElement(xtv, "programme")
            xprogramme.set("start", format_datetime_to_xmltv(p.timer.get_start_datetime()))
            xprogramme.set("stop", format_datetime_to_xmltv(p.timer.get_end_datetime()))
            xprogramme.set("channel", c.name)
            ET.SubElement(xprogramme, "title").text = p.title
            ET.SubElement(xprogramme, "desc").text = p.desc

    tree = ET.ElementTree(xtv)
    tree.write(save_path, encoding="utf-8")
    print("XMLTV saved to {}".format(save_path))


def main():
    today = datetime.date.today()
    days = 3
    for day_offset in range(days):
        day = today + datetime.timedelta(days=day_offset)
        process_day(day)

    build_xml()


if __name__ == '__main__':
    save_path = args.save_path
    days = args.days
    main()
