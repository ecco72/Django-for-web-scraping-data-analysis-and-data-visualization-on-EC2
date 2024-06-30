const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const path = require('path');
const app = express();
const port = 3000;

app.set('view engine', 'ejs');  // 使用ejs進行render
app.set('views', path.join(__dirname, '../templates'));  // 同目錄下的views資料夾內

app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

app.get('/submit-form/', async (req, res) => {
    try {
        let p = req.query.p;
        let area = req.query.area;
        let startp = req.query.startp ? parseInt(req.query.startp) : 0;
        let endp = req.query.endp ? parseInt(req.query.endp) : 50000;

        // 透過API請求數據
        const response = await axios.get('http://54.250.56.245:8888/api-search/', {
            params: {
                p: p,
                area: area,
                startp: startp,
                endp: endp
            }
        });
        
        console.log('API 回應狀態:', response.status);
        console.log('API 回應數據:', response.data);

        // 提取响应中的数据
        const result = response.data.map(item => ({
            title: item.title,
            price: item.price,
            link_url: item.link_url,
            photo_url: item.photo_url,
            loc: item.loc,
            rate: item.rate,
            currency: item.currency
        }));

        // 使用提取的数据渲染hotels.html模板
        res.render('hotels', { result });
    } catch (error) {
        console.error('獲取資料時錯誤:', error.message);
        if (error.response) {
            console.error('錯誤回應數據:', error.response.data);
            console.error('錯誤回應狀態:', error.response.status);
            console.error('錯誤回應頭:', error.response.headers);
            res.status(500).send('獲取資料時錯誤: ' + JSON.stringify(error.response.data));
        } else {
            res.status(500).send('獲取資料時錯誤: ' + error.message);
        }
    }
});

app.listen(port, () => {
    console.log(`伺服器運行在 http://localhost:${port}`);
});
