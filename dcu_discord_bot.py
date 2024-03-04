import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup

#ver 0.11


#'공지'가 아닌 가장 최근의 공지의 숫자형을 출력(봇 시작시에만 사용)
# ex) 시작 번호가 100일 때, 만약 공지가 2개 동시에 올라오면 102번이 가장 최근걸로 인삭하는 오류를 범함
#   -> 맨 첫번째 페이지에서 td테그 안에 '공지' 인것을 제외한 가장 첫번째 수자형을 출력하는 함수.
#   -> 기본적으로 html의 테그 안에 값은 str 타입이기에 숫자로 변환 가능한 첫번째 값을 찾는 함수.
def get_latest_post_number():
    url = "https://www.cu.ac.kr/plaza/notice/lesson"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    i = 0
    while True:
        tr_tags = soup.find('div', class_='board_list').find_all('tr')
        if i >= len(tr_tags):
            break
        post_number_tag = tr_tags[i].find('td')
        if post_number_tag is None:
            i += 1
            continue
        if post_number_tag.text.strip().isdigit():
            latest_post_number = int(post_number_tag.text.strip())
            return latest_post_number
        else:
            i += 1
            continue
    return None

def get_total_post():
    url = 'https://www.cu.ac.kr/plaza/notice/lesson'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    #strong 테그 안에 값을 가져옴 <- 총 게시물
    total_posts = soup.find('div', class_='board_info').find('strong').text
    return total_posts

def get_latest_post_url(num):
    url = 'https://www.cu.ac.kr/plaza/notice/lesson'
    baseurl = 'https://www.cu.ac.kr/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    board_list_div = soup.find('div', class_='board_list')

    if board_list_div:
        # <div> 태그 안에 있는 <table> 태그를 찾음
        table = board_list_div.find('table')
        
        if table:
            # <table> 태그 안에 있는 모든 <td> 태그를 찾음
            for td in table.find_all('td'):
                # 태그 텍스트 값이 latest_post_number(시작번호) 과 일치하는 경우
                if td.text.strip() == str(num):
                    # 해당 태그의 부모인 <tr> 태그를 찾음
                    tr_parent = td.find_parent('tr')
                    # <tr> 태그의 두 번째 <td> 태그를 찾음
                    second_td = tr_parent.find_all('td')[1]
                    # 두 번째 <td> 태그 안에 있는 <a> 태그의 href 속성 값을 출력
                    link_href = second_td.find('a')['href']
                    #게시물의 제목을 가져옴
                    link_title = second_td.find('a').text
                    break
        else:
            print("No table found inside the board_list div.")
    else:
        print("No board_list div found.")

    latest_post_url = f"https://www.cu.ac.kr{link_href}"
    return latest_post_url, link_title


#디스코드 봇 클라이언트 세팅
intents = discord.Intents.default()
intents.typing = False
intents.presences = False

#txt 파일로 TOKEN,GUILD_ID,CHANNEL_ID 읽기
secret = []
f = open("dcu.txt", "r")
for line in f.readlines():
    secret.append(line)
f.close()
TOKEN = secret[0]
GUILD_ID = secret[1]
CHANNEL_ID = secret[2]

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Welcome {bot.user}. The bot has started!')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    channel = discord.utils.get(guild.text_channels, id=CHANNEL_ID)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="NewJeans - Hype Boy"))
    announce_sender.start(channel)
    global latest_post_number

#봇 시작 시 최근 공지 번호
startPostNum = get_latest_post_number()
print(f"시작 공지번호 : {startPostNum}")

@tasks.loop(minutes=0.1)
async def announce_sender(channel):
    new_post_number = get_total_post()

    global startPostNum
    if int(new_post_number) > startPostNum:
        startPostNum += 1
        url, title = get_latest_post_url(startPostNum)
        print("새로운 게시물이 올라왔습니다.")

        #Discord 로 새로운 게시물 전송
        announce_info = f"게시물 번호: {startPostNum}\n게시물 제목: {title.strip()}\n게시물 URL: {url}\n"
        await channel.send(embed=discord.Embed(title=title, description=announce_info))
    else:
        print("Waiting for new post...\n")
        
#봇 시작        
bot.run(TOKEN)