from base64 import b64encode, b64decode
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from hashlib import sha256
from smtplib import SMTP
from urllib.parse import urljoin
import urllib.request

def summarize_site(index_url):
    summary = {}
    baslik = []
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) ' \
             'Gecko/20071127 Firefox/2.0.0.11'
    req = urllib.request.Request(index_url, headers={'User-Agent': user_agent})
    with urllib.request.urlopen(req) as page_req:
                fingerprint = sha256()
                soup = BeautifulSoup(page_req.read(),"lxml")
                manset = soup.find(id="mansetX0").text
                for div in soup.find_all('a', class_='baslik'):
                    fingerprint.update(div.encode())
                summary[index_url] = fingerprint.digest()
    return summary, manset, soup

def save_site_summary(filename, summary):
    with open(filename, 'wt', encoding='utf-8') as f:
        for path, fingerprint in summary.items():
            f.write("{} {}\n".format(b64encode(fingerprint).decode(), path))

def load_site_summary(filename):
    summary = {}
    with open(filename, 'rt', encoding='utf-8') as f:
        for line in f:
            fingerprint, path = line.rstrip().split(' ', 1)
            summary[path] = b64decode(fingerprint)
    return summary

def diff(old, new):
    return {
        'eklendi': new.keys() - old.keys(),
        'silindi': old.keys() - new.keys(),
        'degisti': [page for page in set(new.keys()).intersection(old.keys())
                     if old[page] != new[page]],
    }

def describe_diff(diff, soup):
    desc = []
    for change in ('eklendi', 'silindi', 'degisti'):
        if not diff[change]:
            continue
        desc.append('{} bro :{}\n\n{}'.format(
            change,
            '\n'.join(' ' + path for path in sorted(diff[change])),
            '\n\n'.join(' ' + div['href'] for div in soup.find_all('a', class_='baslik'))
        ))
    return '\n\n'.join(desc)

def send_mail(body, manset):
    fromaddr = "FROMADDR"
    toaddr = "TOADDR"
    msg = MIMEText(body, 'plain')
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = manset
    server = SMTP('smtp.mail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("FROMADDR", "password")
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()

def main(index_url, filename):
    summary, manset, soup = summarize_site(index_url)
    try:
        prev_summary = load_site_summary(filename)    
        if prev_summary:
            diff_description = describe_diff(diff(prev_summary, summary), soup)
            if diff_description:
                print(diff_description)
                send_mail(diff_description, manset)
    except FileNotFoundError:
        pass
    save_site_summary(filename, summary)

main(index_url='http://www.site.com/',
     filename='site.txt')
