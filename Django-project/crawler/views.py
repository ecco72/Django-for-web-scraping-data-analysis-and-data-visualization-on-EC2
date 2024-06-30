from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from .form import RegistrationForm, LoginForm
from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse, HttpResponseRedirect
from django.db import connection
from django.db.models import Avg, Count, Min, Max, F, ExpressionWrapper, FloatField
from .models import AgodaData
from .serializers import AgodaDataSerializer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service   # 抓取chromedriver路徑
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException  # 網頁可能在selenium執行cdp之後還有請求，會導致出現這個錯誤
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json, time, io, subprocess
from urllib import parse  # response下載的utf-8檔名需要透過quote轉換
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pyvirtualdisplay import Display
import twder

def login_view(request):
    if request.user.is_authenticated:
        return redirect('crawl_form')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, '成功登入！')
                return redirect('crawl_form')  # 跳轉到首頁或任何你想要的頁面
            else:
                messages.error(request, '無效的用戶名稱或密碼。')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '成功註冊！請登入。')
            return redirect('login')  # 註冊成功後跳轉到登入頁面
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, '成功登出。')
    return redirect('login')

# 搜尋頁面透過表格POST資料出去 HTML內的action="/POST_crawl/" 決定了POST到哪個網址
@login_required
def crawl_form(request):
    return render(request, 'form.html')   #首頁 form.html為搜尋頁面表單

# 上述的表格資料POST過來這個函式，此為爬蟲的主要程式碼
def POST_crawl(request):
    if request.method == "POST":

        city = request.POST['city']
        checkin = request.POST['checkin']
        checkout = request.POST['checkout']
        adults = request.POST['adult']
        rooms = request.POST['room']

        AgodaData.objects.all().delete() # 清除資料庫表格(因為訂房有時效性)
        
        mcheckin = datetime.strptime(checkin, '%Y-%m-%d')   # 為了算出los(住幾天) 日期轉換
        mcheckout = datetime.strptime(checkout, '%Y-%m-%d')
        los = mcheckout-mcheckin
        los = los.days

        url= "https://www.agoda.com/zh-tw/search?city={}&locale=zh-tw&checkIn={}&checkOut={}&rooms={}&adults={}&children=0&sort=priceLowToHigh".format(city,checkin,checkout,rooms,adults)
        urlfront = 'https://www.agoda.com/zh-tw'
        urlback= "?finalPriceView=1&isShowMobileAppPrice=false&cid=-1&numberOfBedrooms=&familyMode=false&adults={}&children=0&rooms={}&maxRooms=0&isCalendarCallout=false&childAges=&numberOfGuest=0&missingChildAges=false&travellerType=3&showReviewSubmissionEntry=false&currencyCode=TWD&isFreeOccSearch=false&isCityHaveAsq=false&los={}&checkin={}".format(adults,rooms,los,checkin)

        options = Options()
        options.binary_location = '/usr/bin/chromium-browser'
        
        options.add_argument('--no-sandbox')
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=80,60")
        chrome_prefs = {"profile.managed_default_content_settings.images": 2,
                        "profile.managed_default_content_settings.stylesheets": 2,
                        "profile.managed_default_content_settings.autoplay": 2
                        }
        options.experimental_options["prefs"] = chrome_prefs

        caps = {                          # 開啟日誌監聽
                "browserName": "chrome",
                'goog:loggingPrefs': {'performance': 'ALL'},
                }
        for key, value in caps.items():  # 將caps加入到options中
            options.set_capability(key, value)

        display = Display(visible=0, size=(80, 60))
        display.start()
        print("Xvfb display started successfully.")
        service = Service("/usr/bin/chromedriver")
        browser = webdriver.Chrome(service=service, options=options)
        print("Chromium version:", browser.capabilities['browserVersion'])
        print("ChromeDriver version:", browser.capabilities['chrome']['chromedriverVersion'])
        browser.get(url)
        print("Start crawling.")

        while True:    # 滾動頁面 並且切換到下一頁
            for i in range(22):
                browser.implicitly_wait(5)  # 避免未讀取完畢導致錯誤
                browser.execute_script('window.scrollBy(0,1650)')
                time.sleep(1)
                print("Scrolling~~")
                go_or_not = browser.execute_script("return (window.innerHeight + window.scrollY) >= document.body.offsetHeight;")
                i+1
                if go_or_not:
                    break
            soup = BeautifulSoup(browser.page_source,'html.parser')
            
            no_rooms = soup.find("div", {"class": "zero-page"})
            if no_rooms != None:
                print('No more rooms. Finish cralwing. Now processing data.')
                break
            else:
                topbutton = soup.find(id = 'paginationContainer')
                if topbutton.find(id = 'paginationNext') != None:   # 下一頁按鈕
                    browser.execute_script("document.getElementById('paginationNext').click()")
                    print('Going to next page.')
                    time.sleep(3)
                else:
                    print('No more pages. Finish cralwing. Now processing data.')
                    break

        def filter_type(_type: str):   # 設定要過濾的type
            types = [
                'application/javascript', 'application/x-javascript', 'text/css', 'webp', 'image/png', 'image/gif',
                'image/jpeg', 'image/x-icon', 'application/octet-stream', 'image/svg+xml', 'image/webp', 'text/html',
                'font/x-woff2','text/plain'
                ]
            if _type not in types:
                return True
            return False

        print("Start data processing.")
        performance_log = browser.get_log('performance') # 獲取名稱為 performance 的日誌

        # 使用集合避免重複資料
        data_to_insert = set() 
        for packet in performance_log:
            message = json.loads(packet.get('message')).get('message') # 獲取message的數據
            if message.get('method') != 'Network.responseReceived': # 如果method 不是 responseReceived 就不往下執行
                continue
            packet_type = message.get('params').get('response').get('mimeType') # 獲取response的type
            if not filter_type(_type=packet_type): # 過濾type
                continue
            requestId = message.get('params').get('requestId')
            url = message.get('params').get('response').get('url') # 獲取response的url
            if url != 'https://www.agoda.com/graphql/search':
                continue
            
            try:
                resp = browser.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId}) # 使用 Chrome Devtools Protocol
                json_data = resp['body']  # 使用resp讀取抓取到的json檔案
                currency_show = 'JPY'
                if '{"data":{"citySearch":{"featuredPulseProperties":' in json_data: # 爬取json內資料
                    agoda = json.loads(json_data)
                    special = agoda['data']['citySearch']['featuredPulseProperties']
                    for s in special:
                        name = s['content']['informationSummary']['displayName'].replace("'","''")
                        area = s['content']['informationSummary']['address']['area']['name']
                        rating = s['content']['informationSummary']['rating']
                        link = urlfront + s['content']['informationSummary']['propertyLinks']['propertyPage'] + urlback
                        currency_show = s['pricing']['offers'][0]['roomOffers'][0]['room']['pricing'][0]['currency']
                        price = s['pricing']['offers'][0]['roomOffers'][0]['room']['pricing'][0]['price']['perRoomPerNight']['exclusive']['display']
                        img = 'https:'+s['content']['images']['hotelImages'][0]['urls'][0]['value']

                        all_agoda_data = AgodaData(title=name, price=price, loc=area, link_url=link, photo_url=img, rate=rating, currency=currency_show, platform='agoda')
                        data_tuple = (all_agoda_data.title, all_agoda_data.price, all_agoda_data.loc, all_agoda_data.link_url, all_agoda_data.photo_url, all_agoda_data.rate, all_agoda_data.currency, all_agoda_data.platform)                          
                        data_to_insert.add(data_tuple)

                    normal = agoda['data']['citySearch']['properties']
                    for n in normal:
                        name = n['content']['informationSummary']['displayName'].replace("'","''")  #單個引號為跳脫字元 改為雙引號
                        area = n['content']['informationSummary']['address']['area']['name']
                        rating = n['content']['informationSummary']['rating']
                        img = 'https:'+ n['content']['images']['hotelImages'][0]['urls'][0]['value']
                        if n['content']['informationSummary'].get('propertyLinks') != None:
                            link = urlfront + n['content']['informationSummary']['propertyLinks']['propertyPage'] + urlback
                        else:
                            link='https://error'
                        if n['pricing']['isAvailable'] == False:
                            price = '0'
                            currency_show = 'JPY'
                        else:
                            currency_show = n['pricing']['offers'][0]['roomOffers'][0]['room']['pricing'][0]['currency']
                            price = n['pricing']['offers'][0]['roomOffers'][0]['room']['pricing'][0]['price']['perRoomPerNight']['exclusive']['display']

                        if currency_show == None:
                            all_agoda_data = AgodaData(title=name, price=price, loc=area, link_url=link, photo_url=img, rate=rating, currency='JPY', platform='agoda')
                        all_agoda_data = AgodaData(title=name, price=price, loc=area, link_url=link, photo_url=img, rate=rating, currency=currency_show, platform='agoda')
                        data_tuple = (all_agoda_data.title, all_agoda_data.price, all_agoda_data.loc, all_agoda_data.link_url, all_agoda_data.photo_url, all_agoda_data.rate, all_agoda_data.currency, all_agoda_data.platform)                          
                        data_to_insert.add(data_tuple)
                                           
            except WebDriverException:    #網頁可能在程式執行cdp之後還有請求，會導致出現這個錯誤，因為要抓的<search> json 在執行cdp前就已讀取完畢，可以忽略這個錯誤
                pass
        unique_data_to_insert = [AgodaData(title=t[0], price=t[1], loc=t[2], link_url=t[3], photo_url=t[4], rate=t[5], currency=t[6], platform=t[7]) for t in data_to_insert]
        AgodaData.objects.bulk_create(unique_data_to_insert)
        if currency_show == 'JPY':
            AgodaData.objects.update(price=ExpressionWrapper(F('price') * float(twder.now('JPY')[2]), output_field=FloatField()))
            AgodaData.objects.update(currency='TWD')
        print("Finish data processing.") 

        print("Clearing memory cache")
        try:
            subprocess.run(['sudo', 'sync'])
            subprocess.run(['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'])
            print("Memory cache cleared successfully.")
        except Exception as e:
            print(f"Error clearing memory cache: {e}")

        # 將Agoda網站回傳的不合理訂房資料刪除(價格為0、沒有訂房連結、重複的房間、公寓或是臥室價格大於8000、飯店價格大於50000)
        AgodaData.objects.filter(price='0').delete()
        AgodaData.objects.filter(link_url='https://error').delete()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM all_rooms_data where id not in (select * from (SELECT min(id) from all_rooms_data GROUP by title) as a)")
            cursor.execute("DELETE FROM all_rooms_data where (title like '%公寓%' and price > 8000) or (price > 50000) or (title like '%臥室%' and price > 8000) or (title like '%Apartment%' and price > 8000)")
        browser.delete_all_cookies()
        browser.quit() # 關閉爬蟲的網頁
        display.stop()
        return render(request,'search_form.html')   #首頁 form.html為搜尋頁面表單

# 建立過濾器
class AgodaDataList(generics.ListAPIView):
    serializer_class = AgodaDataSerializer

    def get_queryset(self):
        queryset = AgodaData.objects.all()

        # 獲取查詢參數
        p = self.request.query_params.get('p',' ')
        print(p)
        area = self.request.query_params.get('area',' ')
        print(area)
        if self.request.query_params.get('startp') =='':
            startp = 0
        else:
            startp = int( self.request.query_params.get('startp'))
            print(startp)
        
        if self.request.query_params.get('endp') =='':
            endp = 50000
        else:
            endp = int(self.request.query_params.get('endp'))
            print(endp)

        # 過濾
        if p != ' ':
            queryset = queryset.filter(title__icontains=p)
        if area != ' ':
            queryset = queryset.filter(loc__icontains=area)
        queryset = queryset.filter(price__gte=startp, price__lte=endp)

        return queryset

# 下載CSV的連結程式碼，透過ORM將資料庫內的資料抓取下來並且寫入到CSV內，並建立下載的response
def getCSV(request):
    rawdata = AgodaData.objects.all().order_by('price').values('title', 'price', 'link_url', 'loc', 'rate')
    result = list(rawdata)

    title = '飯店名稱,每間每晚價格,訂房連結,區域,星級\n'
    content = ''
    for row in result:
        content = content + row['title'].replace(',','')+','+str(row['price'])+','+row['link_url']+','+row['loc']+','+str(row['rate'])+'\n'  #有些飯店名稱有逗號 要取代掉
        
    csv_content = title + content
    prefilename = datetime.now().strftime("%Y%m%d%H%M")+'訂房查詢資料'
    filename = parse.quote(prefilename) + '.csv'

    bom = '\ufeff'
    response = HttpResponse(bom + csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response

# 畫圖的程式碼，這邊對於資料庫的抓取是使用django.db的函式庫，透過這個函式庫可以直接使用SQL的指令進行操作，畫圖完後儲存至draw_plot/內，方面在html內透過src將圖片帶入
def draw_plot(request):
    fontManager.addfont('/home/ubuntu/agoda/src/app/crawler/TaipeiSansTCBeta-Regular.ttf')
    plt.rc('font', family='Taipei Sans TC Beta')
    plt.rcParams['axes.unicode_minus'] = False
    def img(sqlcmd):
        areasql = f"select loc,{sqlcmd} from all_rooms_data GROUP BY loc ORDER BY COUNT(loc)"

        # 使用django.db的函式庫
        with connection.cursor() as cursor:
            cursor.execute(areasql)
            arearesult = cursor.fetchall()
        
        hotelprice = []
        hotelarea = []
        
        for a in arearesult:
            hotelarea.append(a[0])
            hotelprice.append(a[1])
    
        if sqlcmd == 'COUNT(loc)':
            ax1 = fig.add_subplot(411)
            ax1.bar(hotelarea,hotelprice,zorder=2)
            ax1.grid(zorder=0)
            ax1.set_title('各區域飯店空房數', fontsize='20')
            
        elif sqlcmd == 'avg(price)':
            ax2 = fig.add_subplot(412)
            ax2.bar(hotelarea,hotelprice,zorder=2)
            ax2.grid(zorder=0)
            ax2.set_title('各區域飯店平均價', fontsize='20')
            
        elif sqlcmd == 'max(price)':
            ax3 = fig.add_subplot(413)
            ax3.bar(hotelarea,hotelprice,zorder=2)
            ax3.grid(zorder=0)
            ax3.set_title('各區域飯店最高價', fontsize='20')
            
        else:
            ax4 = fig.add_subplot(414)
            ax4.bar(hotelarea,hotelprice,zorder=2)
            ax4.grid(zorder=0)
            ax4.set_title('各區域飯店最低價', fontsize='20')

    fig = plt.figure(figsize=(20,32))
    img('COUNT(loc)')
    img('avg(price)')
    img('max(price)')
    img('min(price)')
    fig.tight_layout(pad=5)  #子圖間距

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    response = HttpResponse(output.getvalue(), content_type='image/png')
    return response

# 透過ORM將下列三個條件的資料抓取出來，最後使用plot.html將上一個函式的圖片帶入、此程式的資料帶入
def plot(request):
    #平均價格最便宜區域: xx元
    queryset = AgodaData.objects.values('loc', 'currency').annotate(avg_price=Avg('price')).order_by('avg_price')[:1]
    avgcheap = list(queryset)

    #平均價格最貴區域: xx元
    queryset = AgodaData.objects.values('loc', 'currency').annotate(avg_price=Avg('price')).order_by('-avg_price')[:1]
    avgexpensive = list(queryset)
    
    #空房最多區域: xx間
    queryset = AgodaData.objects.values('loc', 'currency').annotate(count=Count('*')).order_by('-count')[:1]
    emptyroom = list(queryset)
    return render(request, 'plot.html', locals())

# 透過ORM將以下的資料抓取出來
def recommendation(request):    
    
    #全區最便宜5間
    queryset = AgodaData.objects.order_by('price')[:4]
    mostcheap = list(queryset)
    
    #全區最貴5間
    queryset = AgodaData.objects.order_by('-price')[:4]
    mostexpensive =list(queryset)

    #各區最便宜
    queryset = AgodaData.objects.values('loc','currency').annotate(title=Min('title'),min_price=Min('price'),link_url=Min('link_url'),photo_url=Min('photo_url'),rate=Min('rate'))
    areacheap = list(queryset)

    #各區最貴
    queryset = AgodaData.objects.values('loc','currency').annotate(title=Max('title'),max_price=Max('price'),link_url=Max('link_url'),photo_url=Max('photo_url'),rate=Max('rate'))
    areaexpensive = list(queryset)
    return render(request, 'recommendation.html', locals())

class IsAuthenticatedReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # 允许已认证用户执行 GET 请求
        if request.method == 'GET' and request.user.is_authenticated:
            return True
        # 只有超级用户才能执行 DELETE 请求
        elif (request.method in ['DELETE', 'PUT', 'POST', 'PATCH'] and request.user.is_superuser):
            return True
        # 其他请求返回 False
        return False

# api的views程式碼 下面是使用modelviewset 本身就包含了完整的get,post,put,delete，若是使用GenericAPIView需要自行新增get等功能
class AgodaViewSet(viewsets.ModelViewSet):
    queryset = AgodaData.objects.all()
    serializer_class = AgodaDataSerializer
    permission_classes = [IsAuthenticatedReadOnly]