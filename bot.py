import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import requests
from bs4 import BeautifulSoup
import os
import dataclasses as dc

client = Bot(description="A bot by rassarian#4378", command_prefix="!", pm_help=True)

commit_check_list = {}
commit_memo_list = {}

@dc.dataclass
class Commit:
    repo: str
    user: str
    name: str
    text: str
    hash: str
    link: str

    def to_embed_str(self):
        _, ___, __, user, repo, typ, branch = self.repo.split("/")
        return f"[{user}/{repo}: {branch}]({self.repo}) [commit {self.hash}]({self.link})"


def extract_url(*args):
    _, user, repo, *__ = 'github'.join(args[0].split("github")[1:]).split("/")
    print(user, repo)
    if len(args) >= 2:
        branch = args[1]
    else:
        repo, *branch = repo.split("@")
        if branch == []:
            branch = "master"
    url = f"https://github.com/{user}/{repo}/commits/{branch}"
    return url

@client.event
async def on_ready():
    print('Logged in as ' + client.user.name + ' (ID:' + client.user.id + ') | Connected to ' + str(
        len(client.servers)) + ' servers | Connected to ' + str(len(set(client.get_all_members()))) + ' users')
    print('--------')
    print('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__,
                                                                               platform.python_version()))
    print('--------')
    print('Use this link to invite {}:'.format(client.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8'.format(client.user.id))
    print('--------')
    print('Created by rassarian#4378')

    print("Loading links...")

    for server in client.servers:
        if not os.path.exists(get_file(server)):
            f = open(get_file(server), "w")
            f.close()

    for _, __, files in os.walk("links"):
        print(files)
        for file in files:
            print(file)
            with open("links/"+file) as f:
                server = file.split("-")[0]
                print(server)
                commit_check_list[server] = []
                commit_memo_list[server] = {}
                for line in f.readlines():
                    commit_check_list[server].append(line.strip())
                    commit_memo_list[server][line.strip()] = extract_commits(line.strip())
    print("Loaded")

@client.command()
async def ping(*args):
    await client.say(":ping_pong: Pong!")

def get_file(server):
    return "links/" + server.name + "-links.txt"

@client.command(pass_context = True)
async def unlinkrepo(ctx, *args):
    server = ctx.message.server
    n = get_file(server)
    url = extract_url(*args)
    urls = filter(lambda i: i != url, open(n).readlines())
    with open(n, "w") as f:
        for u in urls:
            f.write(u + "\n")
    print("Unlinked!")

@client.command(pass_context = True)
async def linkrepo(ctx, *args):
    server = ctx.message.server
    url = extract_url(*args)
    with open(get_file(server), "w") as f:
        f.write(url + "\n")
    commit_check_list[server.name].append(url) #(user, branch, repo))
    commit_memo_list[server.name][url] = extract_commits(url) #user, branch, repo)
    await client.send_message(ctx.message.channel, "Linked!")

async def check_commits():
    await client.wait_until_ready()
    await on_ready()
    counter = 0

    while not client.is_closed:
        for server in client.servers:
            channel = discord.utils.get(server.channels, name='general')
            counter += 1
            for url in commit_check_list[server.name]:
                print(url)
                previous = commit_memo_list[server.name][url.strip()] #[u+b+r]
                new = extract_commits(url.strip()) #(u, b, r)
                output = filter(lambda i: i not in previous, new)
                commit_memo_list[server.name][url] = new
                for commit in output:
                    embed = discord.Embed(title="New commit", description="", color=0x00ff00)
                    embed.add_field(name="Field1", value=commit.to_embed_str(), inline=False)
                    await client.send_message(channel, embed=embed)
        await asyncio.sleep(10) # task runs every 60 seconds

def extract_commits(url):
    commits = []
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    for li in soup.find_all("li", class_="commits-list-item"):
        p = li.find_all("p")[0]
        output = ' '.join(map(lambda i: i.text, p.find_all("a")))
        link = "https://github.com" + p.find_all("a", href=True)[0]['href']
        user = li.find_all("a", class_="commit-author")[0]
        time = user.nextSibling.nextSibling
        commits.append(Commit(repo=page.url,
                              user=user,
                              name=output,
                              text="",
                              hash=link.split("/")[-1][:7],
                              link=link))
    return commits


client.loop.create_task(check_commits())
client.run("NDQ2NDkwMzQ3NTQ0MTE3MjQ4.Dd5yLw.uWYZ3AxpRF0nkBXuZEzsewIOvC8")