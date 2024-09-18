import pandas as pd
from predict import predict

df=pd.DataFrame([[10, 20, 30],[20, 10, 30]])
print(df)
model_input=df.iloc[1,:]
print(model_input)

t3= predict(model_input)

print(t3)