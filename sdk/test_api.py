import cryptoengineersdk as ce

if __name__ == "__main__":
    """
    user_token = {'user': 'hector', 'token': 'a9agHyfg5478GfufUfj98534fs4gHh89Ig7v6fG89kJy7U5f5FFhjU88'}
    model_name = "skl_iris_predict"
    version = "1"
    invoke_URL=ce.deploy(user_token, model_name, version)
    
    print(invoke_URL)
    
    """
    user_token = {'user': 'hector', 'token': 'a9agHyfg5478GfufUfj98534fs4gHh89Ig7v6fG89kJy7U5f5FFhjU88'}
    url = "https://et66iz0wzh.execute-api.us-east-1.amazonaws.com/dev/predict"
    res= ce.shutdown(user_token,url)
    print(res)

    #print(get_api_id(url))
    #print(get_api_key(url))
    #print(get_api_name(url))
