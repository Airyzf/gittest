from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_, or_, not_
from db_models import *


def singleton(cls, *args, **kwargs):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return _singleton


@singleton
class DBUtil(object):
    def __init__(self):
        self.engine = create_engine(
            'sqlite:///./aztest.db', echo=True)
        self.metadata = MetaData(self.engine)
        self.table = None
        self.tables = {}

    def load_table(self, tb_name):
        self.table = Table(tb_name, self.metadata, autoload=True)
        return self.table

    def find_all(self, tb):
        result = tb.select().execute()
        return result

    def update(self, tb, col_kw, kw):
        # user_table.update(user_table.c.name=='yzf').execute(name='yzf666')
        ck = None
        cv = None
        for k, v in col_kw.items():
            ck = k
            cv = v

        upd = tb.update().where(tb.columns[ck] == cv)
        self.engine.execute(upd, kw)

    def insert(self, tb, kwargs):
        ins = tb.insert()
        # for k,v in kwargs.items():
        #     print(k,v)

        # user_table.insert().execute(name="admin",password="admin",u_level=0)
        self.engine.execute(ins, kwargs)

    def dispose(self):
        self.engine.dispose()

    # 加载所以数据库表
    def load_all_tables(self):
        utb = self.load_table('user_tb')
        self.tables['user_tb'] = utb
        user_tb = self.find_all(utb)

        atb = self.load_table('agv_tb')
        self.tables['agv_tb'] = atb
        agv_tb = self.find_all(atb)

        ctb = self.load_table('caller_tb')
        self.tables['caller_tb'] = ctb
        caller_tb = self.find_all(ctb)

        stb = self.load_table('sku_tb')
        self.tables['sku_tb'] = stb
        sku_tb = self.find_all(stb)

        ttb = self.load_table('task_tb')
        self.tables['task_tb'] = ttb
        task_tb = self.find_all(ttb)

        pdb = self.load_table('product_tb')
        self.tables['product_tb'] = pdb
        product_tb = self.find_all(pdb)

        users = []
        for a in user_tb:
            m = UserModel()
            m.id = a[0]
            m.name = a[1]
            m.pwd = a[2]
            m.u_level = a[3]
            m.create_dt = a[4]
            users.append(m)

        agvs = []
        for a in agv_tb:
            m = AGVModel()
            m.id = a[0]
            m.agv_id = a[1]
            agvs.append(m)

        callers = []
        for a in caller_tb:
            m = CallerModel()
            m.id = a[0]
            m.caller_id = a[1]
            callers.append(m)

        skus = []
        for a in sku_tb:
            m = SkuModel()
            m.id = a[0]
            m.sku_id = a[1]
            m.sku_type = a[2]
            m.sku_status = a[3]
            m.sku_pos = a[4]
            m.sku_pdt_id = a[5]
            skus.append(m)

        tasks_id=[]
        tasks = []
        for a in task_tb:
            m = TaskModel()
            m.id = a[0]
            m.task_id = a[1]
            m.task_type = a[2]
            m.status = a[3]
            m.idx = a[4]
            m.urgency = a[5]
            m.ori_sku_id = a[6]
            m.des_sku_id = a[7]
            m.caller_id = a[8]

            m.agv_id = a[9] if a[9]!=None else -1
            m.close_time = a[10] if a[10]!=None else -1
            m.used_time = a[11] if a[11]!=None else -1
            m.remain_time = a[12] if a[12]!=None else -1
            m.progress = a[13] if a[13]!=None else -1
            m.agv_velocity = a[14] if a[14]!=None else -1
            m.total_time = a[15] if a[15]!=None else -1

            m.timestamp = a[16]
            # if m.status == 0:  # 只加载未执行的任务
            tasks.append(m)
            tasks_id.append(m.task_id)

        products = []
        for a in product_tb:
            m = ProdutModel()
            m.id = a[0]
            m.pdt_id = a[1]
            # m.pos = a[2]
            m.sn = a[2]
            m.name = a[3]
            m.pdt_date = a[4]
            products.append(m)

        return users, agvs, callers, skus, tasks, products,tasks_id


if __name__ == "__main__":
    dbutil = DBUtil()
    tb = dbutil.load_all_tables()

    # # # dic={'name':'hhh','password':'admin','u_level':0}
    # data = [
    #     {'name':'admon',}
    # ]
    # dbutil.insert(tb,name="admin",password="admin",u_level=0)
    # dbutil.insert(tb,name="admin1",password="admin1",u_level=0)
    # dbutil.insert(tb,name="admin2",password="admin2",u_level=0)
    # ret = dbutil.find_all(tb)
    # for r in ret:
    #     for i in r:
    #         print(i)


# user_table = Table('user_tb',metadata,autoload=True)

# user_table.insert().execute(name="admin",password="admin",u_level=0)
# user_table.insert().execute(name='yzf',password='123456',u_level=1)
# user_table.insert().execute(name='yzf1',password='123456',u_level=1)
# user_table.insert().execute(name='yzf2',password='123456',u_level=1)
# user_table.insert().execute(name='yzd',password='023456',u_level = 1)

# user_table.update(user_table.c.name=='yzf').execute(name='yzf666')

# result = user_table.select(and_(user_table.c.name=='yzf',user_table.c.password=='123456')).execute()
# for u in result.fetchall():
#     print('result: ',u)

# user_table.delete().where(user_table.c.name=='yzf1').execute()

# result = user_table.select().execute()
# for i in result:
#     print(i)
