# Tries out all user IDs until we find one that has recommendations
# different from the default ones.
import requests

local = False
if local:
    url = "http://localhost:8080/recommend/"
else:
    url = "http://fall2023-comp585-5.cs.mcgill.ca:8082/recommend/"


# Assume first recommendation is the default one.
# Returns valid users in the top 10000 profiles
def find_user(max_id=1000000):
    default = requests.get(url + "1").text
    current_id = 2
    valid_users = []
    while current_id < max_id:
        recommendations = requests.get(url + str(current_id)).text
        if recommendations != default:
            print(current_id)
            valid_users.append(current_id)
        current_id += 1
    print(valid_users)


find_user()

values = []
print(len(values))

"""
Some users that work with database1: 
69
125
269
404
408
504
861
1055
1063
1264
"""
