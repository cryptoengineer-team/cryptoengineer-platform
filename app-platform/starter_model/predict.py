import pandas as pd

def predict(model_input):
        """
        Applies a simple linear transformation
        to the input data. For example, y = 2x + 3.
        """
        print(model_input)
        print(type(model_input))
        
        t1=model_input[0]*3
        t2=model_input[1]+2
        if t1>t2:
            t3=model_input[2]+t1
        else:
            t3=model_input[2]+t2

        # Assuming model_input is a pandas DataFrame with one column
        return t3
