FROM python:3-slim
WORKDIR /programas/api-trymicro3
RUN pip3 install flask
RUN pip3 install pymongo
COPY . .
CMD [ "python3", "./app.py" ]
