import pandas as pd
from datetime import datetime, date
import os
import numpy as np
import math


def get_ra(site: pd.Series, time: pd.Series):  # Extract Location-Based RA from Site and Time; Returns Series
    def cos(x):  # element-wise override
        if type(x) in (int, float):
            return math.cos(x)
        elif type(x) is pd.Series:
            x: pd.Series
            return x.map(math.cos)

    def sin(x):
        if type(x) in (int, float):
            return math.sin(x)
        elif type(x) is pd.Series:
            x: pd.Series
            return x.map(math.sin)

    COORDINATE = {
        'IT-Cas': (45.07004722, 8.717522222),
        'JP-Mse': (36.05393, 140.02693),
        'KR-CRK': (38.2013, 127.2506),
        'PH-RiF': (14.14119, 121.26526),
        'US-HRA': (34.585208, -91.751735),
        'US-HRC': (34.58883, -91.751658),
        'US-Twt': (38.1087204, -121.6531),
        'Ru-Bld': (43.13, 131.9),
        'FNL': (0, 0),
        'GRK': (0, 0),
        'CFK': (0, 0)  # TODO: Site 정보 추가
    }

    coord = site.map(lambda x: COORDINATE[x])
    coord_lat = coord.map(lambda x: x[0] * math.pi / 180)

    DOY = time.map(lambda ts: date(int(str(ts)[0:4]), int(str(ts)[4:6]), int(str(ts)[6:8])).timetuple().tm_yday)
    HOUR = time.map(lambda ts: int(str(ts)[-4:-2]))

    Ll = 0
    Ls = 0

    B = 360 * (DOY - 81) / 365 * math.pi / 180
    ET = 9.87 * sin(2 * B) - 7.53 * cos(B) - 1.5 * sin(B)
    ST = HOUR + ET / 60 + 4 / 60 * (Ll - Ls)
    hangle = (ST - 12) * math.pi / 12

    ST0 = HOUR - 1 + ET / 60 + 4 / 60 * (Ll - Ls)
    hangle0 = (ST0 - 12) * math.pi / 12

    DEC = -23.45 * cos(360 / 365 * (DOY + 10) * math.pi / 180) * math.pi / 180
    ISC = -1367 * 3600 / 1000000
    E0 = -1 + 0.0033 * cos(2 * math.pi * DOY / 365)

    Ra_hourly = (12 * 3.6 / math.pi) * ISC * E0 * (
            ((sin(coord_lat) * cos(DEC)) * (sin(hangle) - sin(hangle0))) + (math.pi / 180 * (hangle - hangle0)) *
            (sin(coord_lat) * sin(DEC)))

    return Ra_hourly


def main():
    code = 'LTRU'
    df_per_year = []
    weather_files = [x for x in os.listdir('weather') if x.endswith('.csv')]
    for weather_file in weather_files:
        df: pd.DataFrame
        df = pd.read_csv(os.path.join('weather', weather_file), encoding='euc-kr')
        df = df[['일시', '습도', '강수량', '최고 기온', '최저 기온']]
        df.columns = ['date', 'humidity', 'rain', 'tmax', 'tmin']

        df["time"] = df["date"].map(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime("%Y%m%d%H%M"))
        df["site"] = 'Ru-Bld'

        df['srad'] = get_ra(df['site'], df['time'])
        df['srad'].map(lambda x: x if not x < -1 else -1)
        df['srad'] = 10*(df['srad'] + 0.3)
        df = df.drop(['time', 'site'], axis=1)

        df['date'] = df['date'].map(lambda x: datetime.strptime(x[:len('2018-01-01')], "%Y-%m-%d"))

        df = df.replace(-99.8, np.NAN)
        df = df.replace(-999.0, np.NAN)

        gdf = df.groupby('date')
        temp = []
        for group in gdf:
            date= group[0].timetuple().tm_yday
            data = group[1]
            humidity = group[1]['humidity'].mean()
            srad = data['srad'].mean()

            def agg(ser):
                t = ser.dropna().tolist()
                return sum(t) / len(t) if not t == [] else 0.0

            tmax = agg(data['tmax'])
            tmin = agg(data['tmin'])
            rain = agg(data['rain'])

            temp.append(
                [date, srad, tmax, tmin, humidity, rain]
            )
        temp = pd.DataFrame(temp, columns=['DOY', 'SRAD', 'TMAX', 'TMIN', 'HUMIDITY', 'RAIN'])
        df_per_year.append(temp)

#
        years = [2017, 2018, 2019, 2020, 2021]
        for i, df_yearly in enumerate(df_per_year):
            year = years[i]
            filename = os.path.join('weather', code.upper() + str(year)[2:] + '01.WTH')

            metadata = """
*WEATHER DATA : Lotte Russia

@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT
{INSI}   {LAT}   {LONG}   {ELEV}   {TAV} {AMP}   {REFHT}   {WNDHT}
@DATE  SRAD  TMAX  TMIN  RAIN  DEWP  WIND
    """.format(
                INSI=code.upper(),
                LAT=131.9,
                LONG=43.19,
                ELEV=-99,
                TAV=-99,
                AMP=-99,
                REFHT=-99,
                WNDHT=-99
            )
            with open(filename, 'w') as wth:
                wth.write(metadata)
                for doy, sample in df_yearly.iterrows():
                    line = "{DATE}   {SRAD}   {TMAX}   {TMIN}   {RAIN}   {DEWP}   {WIND}".format(
                        DATE=str(year)[2:] + str(int(sample['DOY'])).zfill(3),
                        SRAD=round(sample['SRAD']*0.8, 2),
                        TMAX=round(sample['TMAX'], 2),
                        TMIN=round(sample['TMIN'], 2),
                        RAIN=round(sample['RAIN'], 2),
                        DEWP=-99,
                        WIND=-99
                    )
                    wth.write(
                        line
                    )
                    wth.write('\n')

main()