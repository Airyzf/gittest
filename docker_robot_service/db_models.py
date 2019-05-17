
class UserModel:
    def __init__(self):
        self.id = None
        self.name = None
        self.pwd = None
        self.u_level = None
        self.create_dt = None


class AGVModel:
    def __init__(self):
        self.id = None
        self.agv_id = None


class CallerModel:
    def __init__(self):
        self.id = None
        self.caller_id = None


class SkuModel:
    def __init__(self):
        self.id = None
        self.sku_id = None
        self.sku_type = None
        self.sku_status = None # 0:空闲,1:占用,2:准备搬入,3:准备搬出
        self.sku_pos = None
        self.sku_pdt_id = None

    def model_update_db(self,dbutil,sku_id,status):
        tb = dbutil.tables['sku_tb']
        colkw = {'sku_id':sku_id}
        kw={'sku_status':status}
        dbutil.update(tb,colkw,kw)


class TaskModel:
    def __init__(self):
        self.id = None
        self.task_id = None
        self.task_type = None# 0:叫料，1:发料
        self.status = None# 0:等待执行,1:正在取货,2:正在放货,3:任务完成
        self.idx = None
        self.urgency = None
        self.ori_sku_id = None
        self.des_sku_id = None
        self.caller_id = None

        self.agv_id = None
        self.close_time = None
        self.used_time = None
        self.remain_time = None
        self.progress = None
        self.agv_velocity = None
        self.total_time = None

        self.timestamp = None

    def model2db(self, dbutil):
        kw = {'task_id': self.task_id, 'task_type':self.task_type,'status': self.status, 'idx': self.idx, 'urgency': self.urgency,
              'ori_sku_id': self.ori_sku_id, 'des_sku_id': self.des_sku_id, 'caller_id': self.caller_id,
              'agv_id':self.agv_id,'timestamp': self.timestamp}

        tb = dbutil.tables['task_tb']
        dbutil.insert(tb, kw)

    def model_update_db(self, dbutil, task_id, status=3):
        tb = dbutil.tables['task_tb']
        colkw = {'task_id':task_id}
        kw = {'status': status}
        dbutil.update(tb, colkw, kw)

    def model_update_common_db(self, dbutil, task_id, kw):
        tb = dbutil.tables['task_tb']
        colkw = {'task_id':task_id}
        # kw = {'status': status}
        dbutil.update(tb, colkw, kw)


class ProdutModel:
    def __init__(self):
        self.id = None
        self.pdt_id = None
        self.pos = None
        self.sn = None
        self.name = None
        self.pdt_date = None


if __name__ == "__main__":
    pid='101,102,103'
    ps=pid.split(',')
    pp='101'
    hh = [pp for p in ps if p==pp]
    print(type(ps))
    





    
