from sqlalchemy import Table, Column, Integer, String, Boolean,MetaData, ForeignKey,create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_,or_,not_
import sqlalchemy

def create_db():
    engine = create_engine('sqlite:///./aztest.db',echo=True)
    metadata=MetaData(engine)

    # 用户表
    user_tb=Table(
        'user_tb',
        metadata,
        Column('id',Integer,primary_key=True,unique=True),
        Column('name',String(30),nullable=False,unique=True),
        Column('password',String(200),nullable=False),
        Column('u_level',Integer,nullable=False),
        Column('create_dt',Integer)
        
    )

    if not user_tb.exists():
        user_tb.create()

    # AGV表
    agv_tb=Table(
        'agv_tb',
        metadata,
        Column('id',Integer,primary_key=True,unique=True),
        Column('agv_id',Integer,nullable=False)
    )

    if not agv_tb.exists():
        agv_tb.create()

    # 呼叫设备表
    caller_tb=Table(
        'caller_tb',
        metadata,
        Column('id',Integer,primary_key=True,unique=True),
        Column('caller_id',Integer,nullable=False)
    )

    if not caller_tb.exists():
        caller_tb.create()

    # 库位表
    sku_tb=Table(
        'sku_tb',
        metadata,
        Column('id',Integer,primary_key=True,unique=True),
        Column('sku_id',String(50),nullable=False),
        Column('sku_type',Integer,nullable=False),# 0：工位，1:仓库
        Column('sku_status',Integer,nullable=False),# 0:空闲,1:占用,2:准备搬入,3:准备搬出
        Column('sku_pos',Integer,nullable=False),# 库位位置
        Column('sku_pdt_id',String,nullable=False),# 存放产品id
    )

    if not sku_tb.exists():
        sku_tb.create()

    # 任务表
    task_tb=Table(
        'task_tb',
        metadata,
        Column('id',Integer,primary_key=True,unique=True,autoincrement=True),
        Column('task_id',Integer,nullable=False),
        Column('task_type',Integer,nullable=False),# 0:叫料，1:发料
        Column('status',Integer,nullable=False),# 0:等待执行,1:正在取货,2:正在放货,3:任务完成
        Column('idx',Integer,nullable=False),
        Column('urgency',Integer,nullable=False),
        Column('ori_sku_id',Integer,nullable=False),
        Column('des_sku_id',Integer,nullable=False),
        Column('caller_id',Integer,nullable=False),

        Column('agv_id',Integer,default=-1),
        Column('close_time',Integer,default=-1),
        Column('used_time',Integer,default=-1),
        Column('remain_time',Integer,default=-1),
        Column('progress',Integer,default=-1),
        Column('agv_velocity',Integer,default=-1),
        Column('total_time',Integer,default=-1),

        Column('timestamp',Integer,nullable=False)
    )

    if not task_tb.exists():
        task_tb.create()

    # 产品表
    product_tb=Table(
        'product_tb',
        metadata,
        Column('id',Integer,primary_key=True,unique=True),
        Column('pdt_id',Integer,nullable=False),
        Column('pos',Integer,nullable=False),
        Column('sn',String(50),nullable=False),
        Column('name',String(50),nullable=False),
        Column('pdt_date',Integer,nullable=False)
    )

    if not product_tb.exists():
        product_tb.create()

    print('create database end')


if __name__ == "__main__":
    create_db()
    print(sqlalchemy.__version__)