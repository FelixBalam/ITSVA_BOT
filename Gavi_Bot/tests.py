user_data = {}
user_data['1'] = {'state':'one'}

def set_name(name):
    user_data['1']['name'] = name
    
set_name("sum1")
print(user_data)