# coding: utf-8


"""工具类型的代码写到这里,这是一个工具类型的模块"""
import configparser
from enum import unique, Enum

import cx_Oracle
import pymysql
import pandas as pd
from dateutil import rrule
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import numpy as np
from pytime import pytime
from sqlalchemy import create_engine, text, Column, BigInteger, DateTime, Numeric, String, Float, Integer, BIGINT, \
    INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import logging

logger = logging.getLogger(__name__)  # __name__=projectA.moduleB


# -------------------------------------config file--------------------------------------------
def time_sequence_table():
    url = read_radar_data_dir('config.ini', 'data-db', 'url')
    username = read_radar_data_dir('config.ini', 'data-db', 'username')
    password = read_radar_data_dir('config.ini', 'data-db', 'password')
    database = read_radar_data_dir('config.ini', 'data-db', 'database')
    return url, username, password, database


def read_radar_data_dir(config_file_name, config_section_name, config_option_name):
    """根据配置文件的名称，配置section的名称和配置option的名称获取目标文件夹"""
    global target_directory
    cf = configparser.ConfigParser()
    # 读配置文件（ini、conf）返回结果是列表
    config_file = cf.read(config_file_name, encoding="utf-8")
    # 获取读到的所有sections(域)，返回列表类型
    config_sections = cf.sections()
    for config_section in config_sections:
        if config_section == config_section_name:
            # 某个域下的所有key，返回列表类型
            config_options = cf.options(config_section)
            for config_option in config_options:
                if config_option == config_option_name:
                    # 获取某个域下的key对应的value值
                    target_directory = cf.get(config_section, config_option)
                    break
            break
    return target_directory


def write_2d_array_to_txt(arrs, txt_file):
    """把二维数组写入到txt文本中,txt_file为txt文件文件名字符串，比如'test.txt'"""
    arr_str = []
    f = open(txt_file, 'w+')
    for i in range(len(arrs)):
        joints_frame = arrs[i]  # 每行
        arr_str.append(joints_frame)
        for j in range(len(joints_frame)):
            strNum = str(joints_frame[j])
            f.write(strNum)
            f.write(' ')
        f.write('\n')
    f.close()


# -------------------------------------database--------------------------------------------
def db_timesequence_by_attribute_time(entity_attribute_id, time_unit_type, time_unit_num,
                                      start_time, end_time):
    """从数据库读取all entities' 历史时间序列数据.
    Parameters
    -----------
    entity_attribute_id表示实体的数据类型id
    time_unit_type表示时段类型
    time_unit_num表示单位时段的时段个数
    start_time和end_time是开始和结束时间
    Returns
    --------
    a list with tuple as its element
    """
    url = read_radar_data_dir('config.ini', 'data-db', 'url')
    username = read_radar_data_dir('config.ini', 'data-db', 'username')
    password = read_radar_data_dir('config.ini', 'data-db', 'password')
    database = read_radar_data_dir('config.ini', 'data-db', 'database')
    connect = create_engine("mysql+pymysql://" + username + ":" + password + "@" + url + ":3306/" + database,
                            encoding="utf-8",
                            echo=True)  # 连接数据库，echo=True =>把所有的信息都打印出来

    Base = declarative_base()  # 生成ORM基类

    class TimeSequence(Base):
        __tablename__ = "t_bd_time_sequence"  # 表名
        id = Column(INTEGER, primary_key=True)  # 不能带长度,否则会出现类型对不上的错误
        ent_id = Column(BIGINT)
        ent_name = Column(String)
        attribute_id = Column(BIGINT)
        attribute_name = Column(String)
        time_step_unit = Column(String)
        time = Column(DateTime)
        time_step_length = Column(BIGINT)
        value = Column(Float)
        description = Column(String)

    # Base.metadata.create_all(connect)  # 创建表结构

    session_class = sessionmaker(bind=connect)  # 创建与数据库的会话session class ,这里返回给session的是个class,不是实例
    session = session_class()  # 生成session实例

    results = session.query(TimeSequence).filter(
        text(
            "attribute_id=:attribute_id and time_step_unit=:time_step_unit and "
            "time_step_length=:time_step_length and time>=:start_time and time<:end_time")).params(
        attribute_id=entity_attribute_id, time_step_unit=time_unit_type,
        time_step_length=time_unit_num, start_time=start_time, end_time=end_time).order_by(
        TimeSequence.ent_id, TimeSequence.time).all()
    logger.debug("获取到的符合条件的记录个数是 '%s'", len(results))
    return results


def read_data_from_db_entity(entity_ids):
    """从数据库读取实体数据.id表示实体id"""
    url = read_radar_data_dir('config.ini', 'data-db', 'url')
    username = read_radar_data_dir('config.ini', 'data-db', 'username')
    password = read_radar_data_dir('config.ini', 'data-db', 'password')
    database = read_radar_data_dir('config.ini', 'data-db', 'database')
    connect = create_engine("mysql+pymysql://" + username + ":" + password + "@" + url + ":3306/" + database,
                            encoding="utf-8",
                            echo=True)  # 连接数据库，echo=True =>把所有的信息都打印出来

    Base = declarative_base()  # 生成ORM基类

    class Entity(Base):
        __tablename__ = "t_be_entity"  # 表名
        id = Column(INTEGER, primary_key=True)  # 不能带长度,否则会出现类型对不上的错误
        name = Column(String)
        type_id = Column(BIGINT)
        description = Column(String)
        longitude = Column(Float)
        latitude = Column(Float)

    # Base.metadata.create_all(connect)  # 创建表结构

    session_class = sessionmaker(bind=connect)  # 创建与数据库的会话session class ,这里返回给session的是个class,不是实例
    session = session_class()  # 生成session实例
    results = session.query(Entity).filter(Entity.id.in_(tuple(entity_ids))).all()
    logger.debug("获取到的符合条件的记录个数是 '%s'", len(results))
    return results


def oracle_select():
    """connect to oracle database, and execute 'select'"""
    '''Note: Set the environment variable PATH to include the path that contains OCI.dll. After that, remeber restart 
    your python IDE ! '''
    url = read_radar_data_dir('config.ini', 'guodian-db', 'url')
    username = read_radar_data_dir('config.ini', 'guodian-db', 'username')
    password = read_radar_data_dir('config.ini', 'guodian-db', 'password')
    conn = cx_Oracle.connect(username + '/' + password + '@' + url + ':1521/ORCL')
    # 使用cursor()方法获取操作游标
    cursor = conn.cursor()
    # 使用execute方法执行SQL语句
    sql = "select * from product_component_version"
    cursor.execute(sql)
    # 使用fetchone()方法获取一条数据
    # data=cursor.fetchone()
    # 获取所有数据
    all_data = cursor.fetchall()
    print(all_data)
    # 获取部分数据，8条
    # many_data=cursor.fetchmany(8)
    # write in another db in your-data-db
    conn.close()


def mysql_sql(url, username, password, database, sql):
    """connect to mysql database, and execute 'select, using pandas and sqlalchemy
    Returns
    -------
    the result's form is pandas' DataFrame
    '"""
    engine = create_engine("mysql+pymysql://" + username + ":" + password + "@" + url + ":3306/" + database,
                           encoding="utf-8",
                           echo=True)  # 连接数据库，echo=True =>把所有的信息都打印出来
    df = pd.read_sql_query(sql, engine)
    return df


def mysql_insert_batch(url, username, password, database, table, params):
    """connect to mysql database, and execute 'insert' in batches"""
    conn = pymysql.connect(url, username, password, database)
    # 使用 cursor() 方法创建一个游标对象 cursor
    cur = conn.cursor()
    '''批量插入数据,sql语句。要注意的是里面的参数，不管什么类型，统一使用%s作为占位符:insert into 表名(参数名1,参数名2) value(%s,%s) parameters: (('param1', 
    'param2'), ('param1', 'param2'))。注意批量添加数据，数据格式必须list[tuple(),tuple(),tuple()]  或者tuple(tuple(),tuple(),tuple()) '''
    params_str = ''
    params_length = len(params)
    if params_length > 0:
        param_length = len(params[0])
        for j in range(param_length):
            if j == param_length - 1:
                params_str = params_str + '%s'
            else:
                params_str = params_str + '%s,'
    try:
        insert_sql = 'insert into ' + table + ' values(' + params_str + ')'
        cur.executemany(insert_sql, params)
    except Exception as e:
        print(e)
        print("sql execute failed")
    else:
        print("sql execute success")
    conn.commit()
    cur.close()
    conn.close()


def mysql_insert_fields_batch(url, username, password, database, table, fields, params):
    """connect to mysql database, and execute 'insert' in batches with given fields"""
    conn = pymysql.connect(url, username, password, database)
    # 使用 cursor() 方法创建一个游标对象 cursor
    cur = conn.cursor()
    '''批量插入数据,sql语句。要注意的是里面的参数，不管什么类型，统一使用%s作为占位符:insert into 表名(参数名1,参数名2) value(%s,%s) parameters: (('param1', 
    'param2'), ('param1', 'param2'))。注意批量添加数据，数据格式必须list[tuple(),tuple(),tuple()]  或者tuple(tuple(),tuple(),tuple()) '''
    params_str = ''
    params_length = len(params)
    fields_str = ''
    if params_length > 0:
        param_length = len(params[0])
        if len(fields) != param_length:
            raise RuntimeError("域的个数和参数个数不一致！请检查！")
        for j in range(param_length):
            if j == param_length - 1:
                params_str = params_str + '%s'
                fields_str = fields_str + fields[j]
            else:
                params_str = params_str + '%s,'
                fields_str = fields_str + fields[j] + ','
    try:
        insert_sql = 'insert into ' + table + '(' + fields_str + ')' + ' values(' + params_str + ')'
        cur.executemany(insert_sql, params)
    except Exception as e:
        print(e)
        print("sql execute failed")
    else:
        print("sql execute success")
    conn.commit()
    cur.close()
    conn.close()


# -------------------------------------date and time--------------------------------------------
@unique
class TimeUnitType(Enum):
    Year = 'Y'  # Year的value被设定为0
    Month = 'M'
    Decad = 'D'
    Week = 'W'
    Day = 'd'
    Hour = 'h'
    Minute = 'm'
    Second = 's'


# 根据开始时间，结束时间和时段类型以及单位时段长，判断时段个数，字符串类型的日期
def time_period_num(start_time, end_time, time_unit_type, time_unit_num):
    a = parse(start_time)
    b = parse(end_time)
    if time_unit_type == TimeUnitType.Year.value:
        return (rrule.rrule(rrule.YEARLY, dtstart=a, until=b).count() - 1) / time_unit_num
    elif time_unit_type == TimeUnitType.Month.value:
        return (rrule.rrule(rrule.MONTHLY, dtstart=a, until=b).count() - 1) / time_unit_num
    elif time_unit_type == TimeUnitType.Decad.value:
        return (rrule.rrule(rrule.DAILY, dtstart=a, until=b).count() - 1) / time_unit_num / 10
    elif time_unit_type == TimeUnitType.Week.value:
        return (rrule.rrule(rrule.WEEKLY, dtstart=a, until=b).count() - 1) / time_unit_num
    elif time_unit_type == TimeUnitType.Day.value:
        return (rrule.rrule(rrule.DAILY, dtstart=a, until=b).count() - 1) / time_unit_num
    elif time_unit_type == TimeUnitType.Hour.value:
        return (rrule.rrule(rrule.HOURLY, dtstart=a, until=b).count() - 1) / time_unit_num
    elif time_unit_type == TimeUnitType.Minute.value:
        return (rrule.rrule(rrule.MINUTELY, dtstart=a, until=b).count() - 1) / time_unit_num
    else:
        return (rrule.rrule(rrule.SECONDLY, dtstart=a, until=b).count() - 1) / time_unit_num


# 已知起始时间和时段长（时段类型和时段个数）求末时刻时间
def cal_end_time(start_time, time_unit_type, time_unit_num):
    a = parse(start_time)
    if time_unit_type == TimeUnitType.Year.value:
        return a + relativedelta(years=+time_unit_num)
    elif time_unit_type == TimeUnitType.Month.value:
        return a + relativedelta(months=+time_unit_num)
    elif time_unit_type == TimeUnitType.Decad.value:
        # TODO(owenyy): 旬的计算加10天不行,暂时这样.用到再补充
        return a + relativedelta(days=+10 * time_unit_num)
    elif time_unit_type == TimeUnitType.Week.value:
        return a + relativedelta(weeks=+time_unit_num)
    elif time_unit_type == TimeUnitType.Day.value:
        return a + relativedelta(days=+time_unit_num)
    elif time_unit_type == TimeUnitType.Hour.value:
        return a + relativedelta(hours=+time_unit_num)
    elif time_unit_type == TimeUnitType.Minute.value:
        return a + relativedelta(minutes=+time_unit_num)
    else:
        return a + relativedelta(seconds=+time_unit_num)


def parse_datetime(str_datetime):
    """for example:'20150801000000' -> '2015-08-02 00:00:00' -> 2015-08-02 00:00:00"""
    str_date = str_datetime[:8]
    str_time = str_datetime[8:10] + ':' + str_datetime[10:12] + ':' + str_datetime[12:14]
    rain_date_time = pytime.parse(str_date + ' ' + str_time)
    return rain_date_time


# -------------------------------------math--------------------------------------------
# 离散一个区间
def discrete_interval(min, max, precision):
    discrete_num = (max - min) / precision + 1
    discrete_values = np.zeros(discrete_num)
    for i in range(0, discrete_num):
        discrete_values[i] = min + precision * i
    return discrete_values
