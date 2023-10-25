#!/usr/bin/env python
# coding: utf-8

# In[38]:


import streamlit as st
import requests
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import threading
import asyncio

def get_weather_forecast(api_key, location):
    url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001'
    params = {
        'Authorization': api_key,
        'locationName': location,
        'elementName': 'Wx,MinT,MaxT,PoP,AT',  # 加入 AT 表示要取得體感溫度資訊
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data['success'] == 'true':
            location_name = data['records']['location'][0]['locationName']
            weather_data = data['records']['location'][0]['weatherElement']

            # 設定初始值為 None
            weather_description = None
            min_temperature = None
            max_temperature = None
            pop = None
            apparent_temperature = None

            for item in weather_data:
                element_name = item['elementName']
                time_data = item['time'][0]
                start_time = time_data['startTime']
                end_time = time_data['endTime']
                parameter_name = time_data['parameter']['parameterName']

                if element_name == 'Wx':
                    weather_description = parameter_name
                elif element_name == 'MinT':
                    min_temperature = parameter_name + '°C'
                elif element_name == 'MaxT':
                    max_temperature = parameter_name + '°C'
                elif element_name == 'PoP':
                    pop = parameter_name + '%'
                elif element_name == 'AT':
                    apparent_temperature = parameter_name + '°C'

            # 將天氣預報資訊存儲在字典中，並返回
            weather_info = {
                'location_name': location_name,
                'start_time': start_time,
                'end_time': end_time,
                'weather_description': weather_description,
                'min_temperature': min_temperature,
                'max_temperature': max_temperature,
                'pop': pop,
                'apparent_temperature': apparent_temperature,
            }

            return weather_info

        else:
            print('無法獲取天氣資料。')
            return None

    except requests.exceptions.RequestException as e:
        print('網路連線錯誤。', e)


def get_weather_data(api_key, city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        weather_data = response.json()
        temperature = weather_data["main"]["temp"]
        max_temp = weather_data["main"]["temp_max"]
        min_temp = weather_data["main"]["temp_min"]
        weather_status = weather_data["weather"][0]["description"]
        humidity = weather_data["main"]["humidity"]
        pressure = weather_data["main"]["pressure"]
        wind_speed = weather_data["wind"]["speed"]
        wind_direction = weather_data["wind"]["deg"]
        sunrise = weather_data["sys"]["sunrise"]
        sunset = weather_data["sys"]["sunset"]

        if "rain" in weather_data:
            rain_probability = weather_data["rain"].get("24h", 0)
        else:
            rain_probability = 0

        return temperature, max_temp, min_temp, weather_status, humidity, pressure, wind_speed, wind_direction, sunrise, sunset, rain_probability

#         return temperature, max_temp, min_temp, weather_status, humidity, pressure, wind_speed, wind_direction, sunrise, sunset

       
    else:
        print("無法獲取天氣資料。")
        return None, None, None, None, None, None, None, None, None, None ,0
    
def kelvin_to_celsius(temperature_kelvin):
    return round(temperature_kelvin - 273.15,1)

def weather_warning(weather_status):
    dangerous_weather = ["Thunderstorm", "Rain", "Snow", "Tornado", "Hurricane"]
    for condition in dangerous_weather:
        if condition.lower() in weather_status.lower():
            return True
    return False

def plot_weather_data(city, temperature_celsius, max_temp_celsius, min_temp_celsius):
    dates = ["現在", "最高", "最低"]
    temperatures = [temperature_celsius, max_temp_celsius, min_temp_celsius]

    plt.figure(figsize=(8, 6))
    plt.plot(dates, temperatures, marker='o', linestyle='-', color='b')
    plt.title(f"{city} 天氣溫度變化")
    plt.xlabel("日期")
    plt.ylabel("溫度 (°C)")
    plt.grid(True)
    plt.show()
    
def plot_rain_probability(city, rain_probability):
    plt.figure(figsize=(8, 6))
    plt.bar(["降雨機率"], [rain_probability], color='b')
    plt.title(f"{city} 降雨機率變化")
    plt.xlabel("日期")
    plt.ylabel("降雨機率 (%)")
    plt.ylim(0, 100)
    plt.grid(True)
    plt.show()

def send_weather_notification (email, city, weather_status, temperature_celsius, max_temp_celsius, min_temp_celsius,
                             humidity, pressure, wind_speed, wind_direction, sunrise_time, sunset_time):
    sender_email = "h54094015@gs.ncku.edu.tw"  #  Gmail 帳戶
    sender_password = "Burgeon910602"  #  Gmail 密碼
    
    subject = f"{city} 今日天氣通知"
    message = f"城市：{city}\n天氣狀態：{weather_status}\n目前溫度：{temperature_celsius:.1f}°C\n最高溫：{max_temp_celsius:.1f}°C\n最低溫：{min_temp_celsius:.1f}°C\n"
    message += f"濕度：{humidity}%\n大氣壓力：{pressure} hPa\n風速：{wind_speed} m/s\n風向：{wind_direction}°\n"
    message += f"日出時間：{sunrise_time}\n日落時間：{sunset_time}"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [email], msg.as_string())
        server.quit()
        print("天氣通知郵件已發送成功！")
    except Exception as e:
        print("天氣通知郵件發送失敗：", e)
        

def main():
    
    st.title("天氣預報應用")
    image_url = 'https://okapi.books.com.tw/uploads/image/2019/08/source/30490-1566890597.jpg'
    st.image(image_url, use_column_width=True)
    api_key_weather_forecast = 'CWB-0B0B28D1-83CE-4852-BCF9-181408B1840C'
    api_key_weather_data = '9140e3539894595b87006d363569e45f'
    
    #city_weather_forecast = st.text_input("請輸入欲查詢的地點名稱(中文)：")
    location_options = ["基隆市" ,"臺北市", "新北市", "桃園市", "新竹市", "新竹縣" , "苗栗縣" , "臺中市", "彰化縣"
                        , "雲林縣" , "嘉義市" , "嘉義縣" , "臺南市" , "高雄市" , "屏東縣" , "宜蘭縣" , "花蓮縣" , "臺東縣" , "金門縣" , "連江縣" , "澎湖縣"]
    city_weather_forecast = st.selectbox("選擇地點", location_options)
    city_weather_data = st.text_input("請輸入欲查詢的地點名稱(英文)：")
    
    weather_info = None

    if st.button("獲取所在地天氣預報"):
        weather_info = get_weather_forecast(api_key_weather_forecast, city_weather_forecast)
        if weather_info:
            # 顯示天氣預報資訊
            st.write(f"地點：{weather_info['location_name']}")
            st.write(f"日期：{weather_info['start_time']} 到 {weather_info['end_time']}")
            st.write(f"天氣狀況：{weather_info['weather_description']}")
            st.write(f"最低溫度：{weather_info['min_temperature']}")
            st.write(f"最高溫度：{weather_info['max_temperature']}")
            st.write(f"降雨機率：{weather_info['pop']}")
            if weather_info.get('apparent_temperature'):
                st.write(f"體感溫度：{weather_info['apparent_temperature']}")
            else:
                st.write("無體感溫度資訊。")



    if st.button("獲取目的地天氣資料"):
        temperature, max_temp, min_temp, weather_status, humidity, pressure, wind_speed, wind_direction, sunrise, sunset, rain_probability = get_weather_data(api_key_weather_data, city_weather_data)
        sunrise_time = datetime.utcfromtimestamp(sunrise).strftime('%Y-%m-%d %H:%M:%S')
        sunset_time = datetime.utcfromtimestamp(sunset).strftime('%Y-%m-%d %H:%M:%S')

        if temperature and weather_status:
            st.write(f"{city_weather_data} 天氣預報")
            st.write(f"目前溫度：{kelvin_to_celsius(temperature)}°C")
            st.write(f"最高溫：{kelvin_to_celsius(max_temp)}°C")
            st.write(f"最低溫：{kelvin_to_celsius(min_temp)}°C")
            st.write(f"天氣狀態：{weather_status}")
            st.write(f"濕度：{humidity}%")
            st.write(f"大氣壓力：{pressure} hPa")
            st.write(f"風速：{wind_speed} m/s")
            st.write(f"風向：{wind_direction}°")
            st.write(f"日出時間：{sunrise_time}")
            st.write(f"日落時間：{sunset_time}")
            
            if weather_warning(weather_status):
                st.warning("天氣警告：天氣狀態不佳，請注意安全！")
                
             # 發送天氣通知
            send_notification = st.checkbox("發送天氣通知", key="send_notification")
            # 增加一個空白元件，等等要放文字
            email = st.text_input("請輸入您的電子郵件地址：")
            latest_iteration = st.empty()
            bar = st.progress(0)
            for i in range(95):
                latest_iteration.text(f'目前進度 {i+5} %')
                bar.progress(i + 10)

                if st.button("發送通知"):
                    email_model = {
                        "email": email,
                        "city": city_weather_data,
                        "weather_status": weather_status,
                        "temperature_celsius": kelvin_to_celsius(temperature),
                        "max_temp_celsius": kelvin_to_celsius(max_temp),
                        "min_temp_celsius": kelvin_to_celsius(min_temp),
                        "humidity": humidity,
                        "pressure": pressure,
                        "wind_speed": wind_speed,
                        "wind_direction": wind_direction,
                        "sunrise_time": sunrise_time,
                        "sunset_time": sunset_time,
                    }
                    try:
                        response = requests.post("http://http:// http://0.0.0.0:8000/send_weather_notification/", json=email_model)
                        if response.status_code == 200:
                            st.success("天氣通知郵件已發送成功！")
                        else:
                            st.error("天氣通知郵件發送失敗。")
                    except requests.exceptions.RequestException as e:
                        st.error("發生錯誤：", e)

if __name__ == "__main__":
    main()


# In[ ]:





# In[ ]:




