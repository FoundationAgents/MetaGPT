# SPO API BACKEND
**This is an SPO API interface that allows you to easily integrate prompt optimization capabilities into your own applications using this backend,This API backend supports task queues, so you can add many tasks, and the program will optimize prompt words in order**

**This code is built based on some modules in metagpt \ ext \ spo. If necessary, you can integrate the code used in metagpt \ ext \ spo into spo_mapi_mackend by yourself**

**I have written a simple graphical operation page using streamlit for this API, metagpt\ext\spo_api_backend\frontend_sample\spo_gui.py。 You can use this tool to easily optimize a large number of prompt words**

*To fully run the functionality I have written, you can execute the code in the following order*

```python
#Start API service
redis-server
celery -A metagpt.ext.spo_api_backend.celery_app worker --loglevel=info --pool=solo
python -m metagpt.ext.spo_api_backend.spo_api

#Launch graphical interface(You need to enter the metagpt \ ext \ spo_api_mackend \ frontend_stample directory and execute the following code)
streamlit run spo_gui.py

```

This feature is built on the metaGPT project and is used to optimize prompt words
MetaGPT project address：https://github.com/FoundationAgents/MetaGPT

The API backend functionality is created by aflyqi
https://github.com/aflyqi

If there are any issues, you can communicate with me via email
2726132097@qq.com