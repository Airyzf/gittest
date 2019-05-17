FROM python:3.6
ADD ./ .
WORKDIR .
RUN pip install -r ./docker_robot_service/requirements.txt
CMD ["python","./docker_robot_service/robot_service.py"]
//55
//55