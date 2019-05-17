from websocket_server import WebsocketServer
from log_util import log_info, log_error
from models import AGVRequest, AGVStatus, CallerRequest
from load_data import DBUtil
from db_models import *
from threading import Lock
import threading
import os
import sys
import json
import time

# agv请求统计
agvs_ask_task = []
# 定时器标志
timer_cnt = False


def open_ws_server():

    def new_client(client, server):
        log_info("{}:{}".format(client['address'][0], client['address'][1]))
        # server.send_message_to_all("Hey all, a new client has joined us")

    def client_left(client, server):
        log_info("Client(%d) disconnected" % client['id'])

    def message_received(client, server, message):
        try:
            log_info('recv: '+message)
            if len(message) > 2 and message.find('cmd') > 0:
                # message = message[:200]+'..'
                # log_info("Client(%d) said: %s" % (client['id'], message))

                # server.send_message_to_all(message)
                print(message)
                recv_data(message, client)
        except Exception as e:
            print(e)
            log_error('message_recv:'+e.args[0])
            js = json.dumps({'cmd': 5, 'dev_type': -1, 'dev_id': -1, 'error': '服务端异常: ' +
                             e.args[0], 'text': message, 'timestamp': get_timestamp()})
            server.send_message(client, js)
            server.send_message_to_all(js)
            # server.send_message(e.args[0], client)

    def recv_data(data, client=None):
        dic = json.loads(data)
        js = ''
        is_error = False
        if 'cmd' not in dic:
            js = json.dumps({'cmd': 5, 'dev_type': -1, 'dev_id': -1,
                             'error': 'json 格式错误', 'text': data, 'timestamp': get_timestamp()})
            is_error = True
            # return

        else:
            cmd = dic['cmd']
            if cmd == 1:
                ret, caller_req, dst_sku, js, iscall_meta, error = get_caller_request(
                    dic)
                if ret == -1:
                    js = json.dumps({'cmd': 5, 'dev_type': 1, 'dev_id': caller_req.caller_id,
                                     'error': error, 'text': data, 'timestamp': get_timestamp()})
                    is_error = True
                elif ret != -1 and dst_sku != None:
                    # generate task,add to tasks and database
                    log_info('start genetate task')
                    generate_task(caller_req, dst_sku,
                                  is_call_meta=iscall_meta)
                    log_info('genetate task end')

            elif cmd == 2:
                t = dic['type']
                if t == 1:
                    ret, error, req = get_robot_request(dic)
                    if ret == -1:
                        is_error = True
                        js = json.dumps({'cmd': 5, 'dev_type': 2, 'dev_id': req.agv_id,
                                         'error': error, 'text': data, 'timestamp': get_timestamp()})
                elif t == 2:
                    get_robot_status(dic, js=data)

            elif cmd == 3:
                pass

            elif cmd == 4:
                t = dic['type']
                if t == 5:
                    agv_id = dic['caller_id']
                    js = {'cmd': 4, 'type': 5, 'caller_id': agv_id, 'beat': 2}
                    js = json.dumps(js)
                elif t == 3:
                    agv_id = dic['agv_id']
                    js = {'cmd': 4, 'type': 3, 'agv_id': agv_id, 'beat': 2}
                    js = json.dumps(js)
                elif t == 4:
                    mntor_id = dic['monitor_id']
                    js = {'cmd': 4, 'type': 4, 'monitor_id': mntor_id, 'beat': 2}
                    js = json.dumps(js)
            else:
                js = json.dumps({'cmd': 5, 'dev_type': -1, 'dev_id': -1,
                                 'error': 'cmd 错误', 'text': data, 'timestamp': get_timestamp()})
                is_error = True

        # js = json.dumps({'error': '1', 'result': '0', 'msg': e})
        if js != None:
            log_info('send: '+js)
            server.send_message(client, js)
            if(is_error == True):
                server.send_message_to_all(js)

        # except Exception as e:
        #     log_error(str(e))
        # js = json.dumps({'error': '1', 'result': '0', 'msg': e})
        # server.send_message_to_all(js)

    # 获取呼叫终端请求，并回复是否同意

    def get_caller_request(dic):
        caller_req = CallerRequest().dic2obj(dic)

        error = ''
        ret = -1
        dst_sku = None
        iscall_meta = False
        sku_status = 0
        global skus
        global tasks

        # result = [sku for sku in skus if sku.sku_id ==
        #           caller_req.request_info.sku_id]
        result = [sku for sku in skus if sku.sku_id ==
                  caller_req.request_info.sku_id]

        if len(result) >= 1:
            # result[3] = sku_isnull
            if result[0].sku_status == 0 and caller_req.request_info.type == 0:  # 叫料
                # 产品表校验是否存在这种产品并找出id
                meta = [pdt for pdt in products if pdt.sn ==
                        caller_req.request_info.desc.sn]
                if len(meta) >= 1:
                    pdt_id = meta[0].pdt_id
                    # 根据id去库位表中查找有存放这种产品的仓库库位

                    # sku_pids = s.sku_pdt_id.split(',')
                    # tmp_skus = [s for s in skus if str(pdt_id) in sku_pids
                    #             and s.sku_status == 1 and s.sku_type == 1]
                    tmp_skus = [s for s in skus if s.sku_status == 1 and s.sku_type == 1]
                    if len(tmp_skus) >= 1:
                        dst_sku = tmp_skus[0]  # 默认选择第一个
                        ret = 1
                        iscall_meta = True
                        sku_status = 1
                    else:
                        error = '库位数据库中没有可以存放此产品的库位'
                else:
                    error = '产品数据库找不到此产品ID'

            elif result[0].sku_status == 1 and caller_req.request_info.type == 1:  # 发料
                meta = [pdt for pdt in products if pdt.sn ==
                        caller_req.request_info.desc.sn]
                if len(meta) >= 1:
                    pdt_id = meta[0].pdt_id
                    # 根据id去库位表中查找能存放这种产品的仓库库位
                    # sku_pids = s.sku_pdt_id.split(',')
                    # tmp_skus = [s for s in skus if str(pdt_id) in sku_pids and s.sku_status == 0 and s.sku_type == 1]
                    tmp_skus = [s for s in skus if s.sku_status == 0 and s.sku_type == 1]
                    if len(tmp_skus) >= 1:
                        dst_sku = tmp_skus[0]  # 默认选择第一个
                        ret = 1
                        sku_status = 1
                    else:
                        error = '库位数据库中没有此产品的存货'
                else:
                    error = '产品数据库找不到此产品ID'
            # 更新紧急程度
            elif caller_req.request_info.type == 2:
                
                for t in tasks:
                    if t.task_type==0:
                        if t.des_sku_id == caller_req.request_info.sku_id and t.status!=3:
                            t.urgency = caller_req.request_info.urgency
                            t.model_update_common_db(dbutil,t.task_id,{'urgency':caller_req.request_info.urgency})

                    elif t.task_type == 1:
                        if t.ori_sku_id == caller_req.request_info.sku_id and t.status!=3:
                            t.urgency = caller_req.request_info.urgency
                            t.model_update_common_db(dbutil,t.task_id,{'urgency':caller_req.request_info.urgency})

            # 取消
            elif caller_req.request_info.type == 3:
                for t in tasks:
                    if t.task_type == 0:
                        if t.des_sku_id == caller_req.request_info.sku_id:
                            t.status = 0
                            t.model_update_common_db(dbutil,t.task_id,{'status':0,'agv_id':-1})
                    elif t.task_type == 1:
                        if t.des_sku_id == caller_req.request_info.sku_id:
                            t.status = 0
                            t.model_update_common_db(dbutil,t.task_id,{'status':0,'agv_id':-1})


            # 更新相应库位为占用
            elif caller_req.request_info.type == 4:
                for s in skus:
                    if s.sku_id==caller_req.request_info.sku_id:
                        s.status=1
                        s.model_update_db(dbutil,s.sku_id,1)

            # 更新相应库位为空
            elif caller_req.request_info.type == 5:
                for s in skus:
                    if s.sku_id==caller_req.request_info.sku_id:
                        s.status=1
                        s.model_update_db(dbutil,s.sku_id,0)
            else:
                error = '相应库位没有存货或没有空库位存放此产品'
        else:
            error = '库位数据库不存在呼叫设备的库位ID'
        # service 2 caller
        ans = {'id': caller_req.request_info.id, 'result': ret, 'sku_id': str(caller_req.request_info.sku_id), 'status': sku_status,
               'error_code': 0, 'error_msg': ''}
        js = json.dumps({'cmd': 1, 'caller_id': caller_req.caller_id,
                         'type': 1, 'timestamp': get_timestamp(), 'answer': ans})
        print(js)
        return ret, caller_req, dst_sku, js, iscall_meta, error

    # 获取AGV请求，并回复是否同意
    def get_robot_request(dic):
        ret = -1
        error = ''
        agv_req = AGVRequest().dic2obj(dic)
        if agv_req == None:
            error = '请求参数错误'
        else:
            global timer_cnt
            # 抢任务
            if agv_req.req_info.action == 1:
                if timer_cnt == False:
                    init_time_counter()
                    timer_cnt = True
                # 统计收到第一个请求后的2秒内所有的请求
                if timer_cnt == True:
                    agvs_ask_task.append(agv_req)
            # 释放任务
            elif agv_req.req_info.action == 2:
                pass
            # 充电请求
            elif agv_req.req_info.action == 3:
                pass
            ret = 1

        # service 2 robot
        # ans = {'id': agv_req.req_info.id, 'result': 1,
        #        'error_code': 0, 'error_msg': ''}
        # js = json.dumps({'cmd': 2, 'agv_id': agv_req.agv_id,
        #                  'type': 1, 'timestamp': get_timestamp(), 'answer': ans})
        # print(js)
        return ret, error, agv_req

    # 获取AGV定时推送的状态信息

    def get_robot_status(dic, js=None):
        # AGV状态广播给监控中心
        if js != None:
            server.send_message_to_all(js)

        agv = AGVStatus().dic2obj(dic)
        global need_update
        global tasks
        interesting_tasks = []
        for ts in agv.task_status:
            for t in tasks:
                if ts.id == t.task_id:
                    interesting_tasks.append(t)

        for task in agv.task_status:
            if task.status in [0, 1, 2, 3]:
                # print(task.id)

                tmp_tasks = tasks.copy()
                ts = [t for t in tmp_tasks if t.task_id == task.id]
                if len(ts) >= 0:
                    m = ts[0]

                    global dbutil
                    # 更新任务表和库位表
                    m.model_update_db(dbutil, task.id, status=task.status)

                    global skus
                    # 任务完成
                    if task.status == 3:
                        # tasks.remove(m)
                        # edit tasks
                        global mutex
                        
                        for t in tasks:
                            if t.task_id == task.id:
                                mutexflag = mutex.acquire(True)
                                if mutexflag:
                                    t.status = 3
                                    mutex.release()
                        
                        ori_des_type_id = [
                            [t.ori_sku_id, t.des_sku_id, t.task_type, t.task_id] for t in interesting_tasks]
                        for (ori, des, ty, tid) in ori_des_type_id:
                            if task.id == tid:
                                for sku in skus:  # 遍历库位更新状态
                                    # 叫料，任务完成，起始库位状态为占用，终点库位为空
                                    if ty == 0 and sku.sku_id == ori:
                                        sku.sku_status = 0
                                        sku.model_update_db(dbutil, ori, 0)
                                        print(
                                            '叫料,任务完成,update sku status {}:0'.format(ori))
                                        if need_update == False:
                                            need_update = True

                                    elif ty == 0 and sku.sku_id == des:
                                        sku.sku_status = 1
                                        sku.model_update_db(dbutil, des, 1)
                                        # print('update sku status {}:1')
                                        if need_update == False:
                                            need_update = True

                                    # 发料，任务完成，起始库位状态为空，终点库位为占用
                                    elif ty == 1 and sku.sku_id == ori:
                                        sku.status = 0
                                        sku.model_update_db(dbutil, ori, 0)
                                        print(
                                            '发料，任务完成，update sku status {}:0'.format(ori))
                                        if need_update == False:
                                            need_update = True

                                    elif ty == 1 and sku.sku_id == des:
                                        sku.status = 1
                                        sku.model_update_db(dbutil, des, 1)
                                        if need_update == False:
                                            need_update = True

                    # 正在放货
                    elif task.status == 2:
                        ori_des_type_id = [
                            [t.ori_sku_id, t.des_sku_id, t.task_type, t.task_id] for t in interesting_tasks]

                        # edit tasks
                        
                        for t in tasks:
                            if t.task_id == task.id:
                                mutexflag = mutex.acquire(True)
                                if mutexflag:
                                    t.status = task.status
                                    mutex.release()

                            for (ori, des, ty, tid) in ori_des_type_id:
                                if t.task_id == tid:
                                    for sku in skus:
                                        # 叫料，正在放货，起始库位状态为空，终点库位为准备搬入
                                        if ty == 0 and sku.sku_id == ori:
                                            sku.sku_status = 0
                                            sku.model_update_db(dbutil, ori, 0)
                                            print(
                                                '叫料，正在放货，update sku status {}:0'.format(ori))

                                            if need_update == False:
                                                need_update = True

                                        elif ty == 0 and sku.sku_id == des:
                                            sku.sku_status = 2
                                            sku.model_update_db(dbutil, des, 2)
                                            print(
                                                '叫料，正在放货，update sku status {}:2'.format(des))
                                            if need_update == False:
                                                need_update = True

                                        # 发料，正在放货，起始库位状态为空，终点库位为准备搬入
                                        elif ty == 1 and sku.sku_id == ori:
                                            sku.sku_status = 0
                                            sku.model_update_db(dbutil, ori, 0)
                                            if need_update == False:
                                                need_update = True

                                        elif ty == 1 and sku.sku_id == des:
                                            sku.sku_status = 2
                                            sku.model_update_db(dbutil, des, 2)
                                            if need_update == False:
                                                need_update = True
                                
                    # 正在取货
                    elif task.status == 1:
                        ori_des_type_id = [
                            [t.ori_sku_id, t.des_sku_id, t.task_type, t.task_id] for t in interesting_tasks]
                        # edit tasks

                        for t in tasks:
                            if t.task_id == task.id:
                                mutexflag = mutex.acquire(True)
                                if mutexflag:
                                    t.status = task.status
                                    mutex.release()

                            for (ori, des, ty, tid) in ori_des_type_id:
                                if t.task_id == tid:
                                    for sku in skus:
                                        # 叫料，正在取货，起始库位状态为准备搬出，终点库位为空
                                        if ty == 0 and sku.sku_id == ori:
                                            sku.sku_status = 3
                                            sku.model_update_db(dbutil, ori, 3)
                                            print(
                                                '叫料，正在放货，update sku status {}:3'.format(ori))
                                            if need_update == False:
                                                need_update = True

                                        elif ty == 0 and sku.sku_id == des:
                                            sku.sku_status = 0
                                            sku.model_update_db(dbutil, des, 0)
                                            print(
                                                '叫料，正在放货，update sku status {}:0'.format(des))
                                            if need_update == False:
                                                need_update = True

                                        # 发料，正在取货，起始库位状态为准备搬出，终点库位为空
                                        elif ty == 1 and sku.sku_id == ori:
                                            sku.sku_status = 3
                                            sku.model_update_db(dbutil, ori, 3)
                                            if need_update == False:
                                                need_update = True

                                        elif ty == 1 and sku.sku_id == des:
                                            sku.sku_status = 0
                                            sku.model_update_db(dbutil, des, 0)
                                            if need_update == False:
                                                need_update = True
                            
    # 获取时间戳
    def get_timestamp():
        return int(round(time.time() * 1000))

    def generate_task(req, dst_sku, is_call_meta=True):
        m = TaskModel()
        m.task_id = get_timestamp()
        m.status = 0
        m.task_type = req.request_info.type
        m.idx = m.task_id
        m.caller_id = req.caller_id
        m.urgency = req.request_info.urgency
        if is_call_meta:
            m.ori_sku_id = dst_sku.sku_id
            m.des_sku_id = req.request_info.sku_id
        else:
            m.ori_sku_id = req.request_info.sku_id
            m.des_sku_id = dst_sku.sku_id

        m.agv_id = -1
        m.close_time = -1
        m.used_time = -1
        m.remain_time = -1
        m.progress = -1
        m.agv_velocity = -1
        m.total_time = -1

        m.timestamp = m.task_id

        global tasks
        # edit tasks
        global mutex
        mutexflag = mutex.acquire(True)
        if mutexflag:
            tasks.append(m)
            mutex.release()

        global tasks_id_arr
        tasks_id_arr.append(m.task_id)

        global dbutil
        m.model2db(dbutil)

    # 给AGV广播任务
    def broadcast_task_agv():
        while brocast_task_flag:
            global tasks
            ts = tasks.copy()
            task_arr_js = []
            js = None
            for t in ts:
                if t.status == 0:
                    task_js = {'task_id': t.task_id, 'status': t.status,
                               'index': t.idx, 'urgency': t.urgency, 'ori_sku_id': str(t.ori_sku_id),
                               'des_sku_id': str(t.des_sku_id)}
                    task_arr_js.append(task_js)

            if len(task_arr_js) > 0:
                js = json.dumps(
                    {'cmd': 2, 'type': 2, 'timestamp': get_timestamp(), 'task_list': task_arr_js})

            if js != None:
                server.send_message_to_all(js)
            time.sleep(brocast_task_time)

    # 给呼叫设备和监控中心广播库位信息
    def broadcast():
        while brocast_sku_flag:
            global skus
            global products
            tmp_skus = skus.copy()
            tmp_pdts = products.copy()
            js = ''
            tmp_caller_js = []
            tmp_mnt_js = []
            update = 0
            global need_update
            if need_update:
                update = 1
            for sku in tmp_skus:

                # sku_pids = sku.sku_pdt_id.split(',')
                # name_sn = [[p.name, p.sn, p.pdt_date]
                #            for p in tmp_pdts if str(p.pdt_id) in sku_pids]
                name_sn = [[p.name, p.sn, p.pdt_date]
                           for p in tmp_pdts]
                name = name_sn[0][0]
                sn = name_sn[0][1]
                date = name_sn[0][2]
                tcjs = {'sku_id': str(sku.sku_id), 'status': sku.sku_status,
                        'product_name': name, 'product_sn': sn}
                tmp_caller_js.append(tcjs)

                desc = {'sn': sn, 'name': name, 'date': date}
                tmntjs = {'sku_type': sku.sku_type, 'sku_id': str(sku.sku_id),
                          'status': sku.sku_status, 'desc': desc}
                tmp_mnt_js.append(tmntjs)

            mnt_js = {'cmd': 3, 'type': 1,
                      'timestamp': get_timestamp(), 'sku_info': tmp_mnt_js}
            mnt_js = json.dumps(mnt_js)
            if mnt_js != None:
                server.send_message_to_all(mnt_js)

            callerjs = {'update': update, 'list': tmp_caller_js}
            js = {'cmd': 1, 'type': 2, 'timestamp': get_timestamp(),
                  'sku_info': callerjs}
            js = json.dumps(js)
            if js != None:
                server.send_message_to_all(js)

            need_update = False
            time.sleep(brocast_sku_time)

    # 给监控中心广播任务信息
    def broadcast_task_mon():
        while brocast_task_mon_flag:
            global tasks
            ts = tasks.copy()
            task_arr_js = []
            js = None
            for t in ts:
                task_js = {'task_id': t.task_id, 'status': t.status,
                           'urgency': t.urgency, 'create_time': t.task_id, 'close_time': t.close_time, 'ori_sku_id': str(t.ori_sku_id),
                           'des_sku_id': str(t.des_sku_id), 'caller_id': t.caller_id, 'agv_id': t.agv_id, 'used_time': t.used_time,
                           'remain_time': t.remain_time, 'task_type': t.task_type,
                           'progress': t.progress, 'agv_velocity': t.agv_velocity, 'total_time': t.total_time}
                task_arr_js.append(task_js)

            js = json.dumps(
                {'cmd': 3, 'type': 2, 'timestamp': get_timestamp(), 'task_info': task_arr_js})

            if js != None:
                server.send_message_to_all(js)

            # js = {'cmd': 5, "type": 1, 'dev_id': 2,
            #       'error_msg': 'low power', 'timestamp': get_timestamp()}
            # server.send_message_to_all(json.dumps(js))
            time.sleep(brocast_task_mon_time)

    def timer_count():
        global timer_cnt
        global agvs_ask_task
        global tasks_id_arr

        all_ask_task_ids = [tid.req_info.task_id for tid in agvs_ask_task]
        ask_task_ids = set(tasks_id_arr) & set(
            all_ask_task_ids)  # 查找不重复的请求task_id列表

        filter_agv_task = []
        for task_id in ask_task_ids:  # agv对这几个task_id感兴趣
            ts = []
            for agv_ask in agvs_ask_task:
                if agv_ask.req_info.task_id == task_id:  # 将相同兴趣的agv归类
                    ts.append(agv_ask)

            filter_agv_task.append(ts)

        task_agv = {}
        for ask_tasks in filter_agv_task:
            max_score = max(a.req_info.score for a in ask_tasks)
            # tmp_agvs = [a for a in agvs_ask_task if a.req_info.score == max_score]
            # print(tmp_agvs[0].agv_id)

            global tasks
            # 批量回复同类AGV的任务请求
            for agv_req in ask_tasks:
                ret = 0
                if agv_req.req_info.score == max_score:
                    ret = 1
                    for t in tasks:
                        if t.task_id == agv_req.req_info.task_id:
                            t.agv_id = agv_req.agv_id
                            task_agv[t.task_id] = agv_req.agv_id

                ans = {'id': agv_req.req_info.id, 'result': ret,
                       'error_code': 0, 'error_msg': ''}
                js = json.dumps({'cmd': 2, 'agv_id': agv_req.agv_id,
                                 'type': 1, 'timestamp': get_timestamp(), 'answer': ans})
                server.send_message_to_all(js)

        # 复位
        agvs_ask_task = []
        timer_cnt = False

        # 删除已经派出去的任务

        # tmp_tasks = tasks.copy()
        for i in ask_task_ids:
            for t in tasks:
                if t.task_id == i:
                    # tasks.remove(t)
                    t.status = -1
                    for k, v in task_agv.items():
                        if t.task_id == k:
                            t.agv_id = v
                            t.model_update_common_db(
                                dbutil, t.task_id, {'agv_id': v})

    def init_time_counter():
        timer_counter = threading.Timer(2, timer_count)
        timer_counter.start()

    brocast_task_time = 2
    brocast_task_flag = 1
    timer_task = threading.Timer(1, broadcast_task_agv)
    timer_task.start()

    brocast_sku_time = 2
    brocast_sku_flag = 1
    time_sku = threading.Timer(1, broadcast)
    time_sku.start()

    brocast_task_mon_time = 2
    brocast_task_mon_flag = 1
    time_mon = threading.Timer(1, broadcast_task_mon)
    time_mon.start()

    server = WebsocketServer(55600, host='127.0.0.1')
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    log_info('open ws successfully 1')
    server.run_forever()
    brocast_task_flag = 0
    brocast_sku_flag = 0
    brocast_task_mon_flag = 0
    log_info('open ws successfully 2')


def load_tbs():
    global users
    global agvs
    global callers
    global skus
    global tasks
    global products
    global tasks_id_arr
    users, agvs, callers, skus, tasks, products, tasks_id_arr = dbutil.load_all_tables()
    # us = [u for u in users if u.name=='admin']
    # # for u in us:
    # print(us[0].u_level)


# 所有任务id列表
tasks_id_arr = [1, 2, 3, 4, 5, 6]
# 设备是否需要更新库位信息
need_update = False
mutex = threading.Lock()

dbutil = DBUtil()
users = None
agvs = None
callers = None
skus = None
tasks = None
products = None

if __name__ == "__main__":
    #load_tbs()
    open_ws_server()
