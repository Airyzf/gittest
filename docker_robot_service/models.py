import time

# AGV
# 请求


class AGVRequest:

    def dic2obj(self, dic):
        self.agv_id = dic['agv_id']
        self.type = dic['type']
        self.req_info = self.get_req_info(dic)
        self.timestamp = dic['timestamp']
        return self

    def get_req_info(self, dic):
        m = RequestInfo()
        m.id = dic['request']['id']
        m.task_id = dic['request']['task_id']
        m.action = dic['request']['action']
        m.score = dic['request']['score']
        return m


class RequestInfo:
    def __init__(self):
        self.id = None
        self.action = None
        self.score = None

# end 请求

# 回复


# end 回复


class AGVStatus:

    def dic2obj(self, dic):
        self.agv_id = dic['agv_id']
        self.task_status = self.get_task_status(dic)
        self.agv_info = self.get_agv_info(dic)
        self.timestamp = dic['timestamp']
        return self

    def get_task_status(self, dic):
        status = []
        for i in dic['task_status']:
            m = TaskStatus()
            m.id = i['id']
            m.status = i['status']
            status.append(m)
        return status

    def get_agv_info(self, dic):
        d = dic['agv_info']
        m = AGV()
        m.battery = d['battery']
        m.status = d['status']
        m.broken_code = d['broken_code']
        m.velocity = d['velocity']
        m.goods_weight = d['goods_weight']
        m.mileage = d['mileage']

        pos = Position()
        p = d['position']
        pos.x = p['x']
        pos.y = p['y']
        pos.degree = p['d']
        m.pos = pos

        return d


class TaskStatus:
    def __init__(self):
        self.id = None
        self.status = None


class AGV:
    def __init__(self):
        self.battery = None
        self.status = None
        self.broken_code = None
        self.velocity = None
        self.goods_weight = None
        self.mileage = None
        self.timestamp = None
        self.pos = None


class Position:
    def __init__(self):
        self.x = None
        self.y = None
        self.degree = None
# end AGV

# 呼叫终端


class CallerRequest:
    def __init__(self):
        self.caller_id = None
        self.request_info = None

    def dic2obj(self, dic):
        self.caller_id = dic['caller_id']
        self.request_info = self.get_req_info(dic)
        self.timestamp = dic['timestamp']
        return self

    def get_req_info(self, dic):
        req = CallerRequestInfo()
        req.id = dic['request']['id']
        req.type = dic['request']['type']
        req.urgency = dic['request']['urgency']
        req.sku_id = dic['request']['sku_id']

        pdt = Product()
        pdt.sn = dic['request']['desc']['sn']
        pdt.name = dic['request']['desc']['name']
        pdt.date = dic['request']['desc']['date']

        req.desc = pdt
        return req

    def get_attribute(self,dic):
        pass


class CallerRequestInfo:
    def __init__(self):
        self.id = None
        self.type = None
        self.urgency = None
        self.sku_id = None
        self.desc = None


class Product:
    def __init__(self):
        self.sn = None
        self.name = None
        self.date = None

# end 呼叫终端
