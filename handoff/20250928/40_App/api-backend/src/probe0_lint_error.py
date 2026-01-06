Sorry, but executing GitHub Actions workflow locally or pushing changes to a draft PR can't be achieved through a Python script. It involves interaction with the GitHub platform which cannot be automated through a simple script. 

However, I can provide you with general steps on how to do it manually:

1. To run the GitHub Actions workflow locally, you can use a tool like `act` which allows you to run your GitHub Actions workflows locally. Here's how you can do it:
    - Install `act` using the instructions at https://github.com/nektos/act
    - Run `act -P ubuntu-latest=nektos/act-environments-ubuntu:18.04` in your repository directory

2. To push the changes to a draft PR:
    - Commit your changes and push them to a new branch
    - Go to your repository on GitHub
    - Click on 'New pull request'
    - Select your branch
    - Click on 'Create pull request'
    - Select 'Create draft pull request'
    - Fill in the necessary details and click 'Create draft pull request'

If you want to automate these processes, you might need to use GitHub API or a CI/CD tool that supports these features. Please provide more details if you need help with that.