testing

Steps I used to Connect to my VM instance. 

Connect to the instance. 

chmod 400 ~/Downloads/AkinatorAuth.pem
ssh -i ~/Downloads/AkinatorAuth.pem ubuntu@Public IP here # Ommiting becuase this is public repo

=======================================

Install Dependencies... 

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip -y

=======================================

Next need to creat venv

python3 -m venv venv
source venv/bin/activate

=======================================

Now we can install dependencies. 

pip install flask pandas plotly yfinance apscheduler pytz xlsxwriter matplotlib

=======================================

Optional, Set python venv to run whenever SSH is initiated. (Should not need to be done again.)

echo 'source ~/venv/bin/activate' >> ~/.bashrc
source ~/.bashrc

=======================================

Upload the scripts to be ran. 

C:\Users\stout\IdeaProjects\AkinatorAssets\src

scp -i ~/Downloads/AkinatorAuth.pem -r ~/IdeaProjects/AkinatorAssets/src/AkinatorAssets_2030Targets_AutoRefresh.py ~/IdeaProjects/AkinatorAssets/src/run_watchlist_scriptv2.py ~/IdeaProjects/AkinatorAssets/src/templates ~/IdeaProjects/AkinatorAssets/src/static ubuntu@Public IP here # Ommiting becuase this is public repo



+++++++++++++++++++++++++++++++++++ 

Updated Script to run off of a simpler command.

If you ssh into the ec2 instance I created simply run 

    sudo systemctl restart akinator

You can check if it is active by 

    systemctl status akinator


+++++++++++++++++++++++++++++++++++++

Github actions workflow "deploy.yml" -> it is currently set to deploy "on push" to main branch. Meaning that code will be deployed when we merge to main....
If you want to test your feature branch you can add your feature branch name to the workflow, and it will deploy when you push to that branch. 

ex 

on:
  push:
    branches:
      - main

Change to: 

on:
  push:
    branches:
      - main
      - feature/<branch_name_here>
