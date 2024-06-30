# Django for web scraping,data analysis,and data visualization on EC2
 
架設EC2 Web伺服器過程：

建立執行個體：
1.	EC2 儀表板
2.	建立新的執行個體
3.	使用ubuntu
4.	選取金鑰對(若沒有的話點選右邊新增，輸入名稱後完成，檔案請保存好)
5.	網路設定都允許(SSH HTTPS HTTP)
6.	啟動執行個體
使用金鑰對前要在windows上的金鑰對檔案->點選右鍵->安全性->進階->停用繼承->移除所有繼承權限->新增->選擇一個主體->下方輸入自己windows的帳號->檢查名稱(畫底線代表有抓到)->確定->確定->套用->確定

連線到執行個體：
1.	EC2首頁點選左側的執行個體
2.	等待剛剛新建的執行個體狀態檢查通過
3.	點選執行個體的ID
4.	點選右上角的連線
5.	連線

設定Django伺服器port：
1.	到EC2頁面
2.	設定安全群組
3.	點選目前使用的執行個體的安全群組
4.	編輯傳入規則
5.	新增規則自訂TCP & port 新增傳入規則(依情況設置，用到幾個port就加幾個)
6.	儲存規則

將Django專案部屬到EC2：
1.	EC2上建立資料夾
2.	在本地電腦powershell要傳入檔案的位置輸入以下指令：
	scp -i 你的key名稱.pem -r src requirments.txt 主機名稱@PublicIPS:路徑
	(-i 代表使用金鑰對, -r 代表遞迴傳遞所有資料夾內的檔案)
	(第一次執行會提示安全性問題是否要連線，輸入yes)
3.	在EC2上cd到Django的目錄
4.	更新並安裝設置虛擬環境需要的Linux套件：
	sudo apt-get update
	sudo apt-get install python3-pip python3-venv 
5.	建立python虛擬環境並啟用：
	python3 -m venv 你的虛擬環境名稱
	source 你的虛擬環境名稱/bin/activate
6.	安裝所需套件：
	pip install -r requirements.txt
7.	安裝MySQL：

--------------------------------------------------------------------------------

 	sudo apt-get install -y pkg-config libmysqlclient-dev
	sudo apt install mysql-server
	sudo systemctl start mysql
	sudo systemctl status mysql
	sudo systemctl restart mysql
	sudo systemctl enable mysql
	ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '密碼';
	FLUSH PRIVILEGES;
	CREATE DATABASE mydatabase;
	SHOW DATABASES;

9.	設定npm(node.js)：
	node.js運作方法 => html表單action="node.js的port/aaa" 送給node.js取得表單內容 get(/aaa) 之後向api請求資料(api的port就是Django的port)

	記得要調整跨域設定 (settings.py內)  (pip install Django-cors-headers)

--------------------------------------------------------------------------------
	# 安裝並新增服務文件
	sudo apt-get install npm
	sudo npm install express body-parser axios path ejs --save
	sudo nano /etc/systemd/system/ node-app.service
---------------------------------------------------------------------------------
 	[Unit]
	Description=Node.js Application
	
	[Service]
	WorkingDirectory=/home/ubuntu/agoda/src/app/node_project
	ExecStart=/usr/bin/node /home/ubuntu/agoda/src/app/node_project/nodeserver.js
	Restart=always
	RestartSec=10
	Environment=NODE_ENV=production
	
	[Install]
	WantedBy=multi-user.target
---------------------------------------------------------------------------------
	# 確認node.js文件已經在上面設定的路徑，更改完後重啟服務(更改ejs也要)
	sudo systemctl enable node-app	
	sudo systemctl daemon-reload
	sudo systemctl restart node-app
 
最終在執行node的server前請確認linux套件是否都已安裝完畢、網址的port是否有設定正確，且若是透過api抓資料可以用postman測試！


9.	增加虛擬內存：
	檢查當前Swap空間
---------------------------
	sudo swapon --show
----------
	# 如果沒有Swap，創建一個Swap文件
	sudo fallocate -l 1G /swapfile
	sudo chmod 600 /swapfile
	sudo mkswap /swapfile
	sudo swapon /swapfile
--------------
	# 確保Swap文件在重啟後仍然有效
	echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
	
11.	設置監管程式(Prometheus)：
----------
	# 安裝Prometheus
	wget https://github.com/prometheus/prometheus/releases/download/v2.39.1/prometheus-2.39.1.linux-amd64.tar.gz
	tar xvf prometheus-2.39.1.linux-amd64.tar.gz
	cd prometheus-2.39.1.linux-amd64
	sudo mv prometheus /usr/local/bin/
	sudo mv promtool /usr/local/bin/
	sudo mkdir -p /etc/prometheus
	sudo mv prometheus.yml /etc/prometheus/
	sudo mkdir -p /var/lib/prometheus
-----------
	# 編輯設定檔案
	sudo nano /etc/prometheus/prometheus.yml
	
---------------------------------------------------------------------------------
	global:
	  scrape_interval: 5s
	scrape_configs:
	  - job_name: 'Django'
		static_configs:
		  - targets: ['使用PublicIPS:8888']
---------------------------------------------------------------------------------
	# 編輯服務設定
	sudo nano /etc/systemd/system/prometheus.service
---------------------------------------------------------------------------------
	[Unit]
	Description=Prometheus
	Wants=network-online.target
	After=network-online.target
	
	[Service]
	User=root
	ExecStart=/usr/local/bin/prometheus --config.file /etc/prometheus/prometheus.yml --storage.tsdb.path /var/lib/prometheus/
	
	[Install]
	WantedBy=multi-user.target
---------------------------------------------------------------------------------
	# 重新整理服務並啟動
	sudo systemctl daemon-reload
	sudo systemctl start prometheus
	sudo systemctl enable prometheus


在Django內urls.py和settings.py要設定prometheus


11.	視覺化查看監管數據(Grafana)：
-------
	# 安裝
	sudo apt install -y software-properties-common wget
	wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
	sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
	sudo apt install grafana
------
	# 啟用
	sudo systemctl start grafana-server
	sudo systemctl enable grafana-server

	# 更改port(依需求，預設3000，刪除分號代表啟用)
	sudo nano /etc/grafana/grafana.ini
 -------
	[server]
	http_port = 3010
 --------
 
執行Django：
1.	到達manage.py的目錄
2.  啟動server
	python manage.py runserver 下方privateIPs:你安全群組設定的PORT
	(若使用Gunicorn啟動，在settings.py目錄下執行：
	gunicorn --workers 3 --bind 172.31.33.67:8888 專案名稱.wsgi:application)
3.	在本機電腦上查看是否成功運作
	在本機電腦瀏覽器網址輸入EC2的PublicIPs:port


架設gunicorn和nginx：
------
	# 安裝
	pip install gunicorn
	sudo apt-get install nginx
-----
	# 啟動server
	gunicorn 專案名稱.wsgi:application
 -----
	# 編輯Nginx配置文件以設置反向代理到Gunicorn服務器的位置
	sudo nano /etc/nginx/sites-available
	
----------------------------------------------------------------------------
	server {
	    listen 80;
	    server_name Django-crawler.com;
	
	    location / {
	        proxy_pass http://172.31.33.67:8888;
	        proxy_set_header Host $host;
	        proxy_set_header X-Real-IP $remote_addr;
	        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	        proxy_set_header X-Forwarded-Proto $scheme;
	    }
	
	    location /static/ {
	        alias /home/ubuntu/agoda/src/app/static;
	    }
	}
----------------------------------------------------------------------------

4.	創建並編輯 Gunicorn 服務單元文件：
----
	sudo nano /etc/systemd/system/gunicorn.service

--------------------------------------------------------------------------------
	[Unit]
	Description=gunicorn daemon
	After=network.target
	
	[Service]
	User=ubuntu
	Group=www-data
	WorkingDirectory=/home/ubuntu/agoda/src/app
	ExecStart=/home/ubuntu/agoda/src/Django/bin/gunicorn --workers 3 --bind 0.0.0.0:8888 app.wsgi:application
	
	[Install]
	WantedBy=multi-user.target
---------------------------------------------------------------------------------

5. 重新加載並啟動
-----
	sudo systemctl daemon-reload
	sudo systemctl start gunicorn
	sudo systemctl start nginx
	sudo systemctl enable gunicorn
	sudo systemctl enable nginx
-------


如果在這些步驟之後仍然遇到問題，可以檢查服務的log


檢查 Gunicorn log：
-------
	journalctl -u gunicorn

檢查 Nginx log：
-------
	# 錯誤log
	sudo tail -f /var/log/nginx/error.log
----
	# 訪問log
	sudo tail -f /var/log/nginx/access.log
