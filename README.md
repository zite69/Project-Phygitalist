# Django template for a new django CMS 4 project

A Django template for a typical django CMS installation with no 
special bells or whistles. It is supposed as a starting point 
for new projects.

If you prefer a different set of template settings, feel free to 
create your own templates by cloning this repo.

To install django CMS 4 by hand type the following commands:

1. Create virtual environment and activate it
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install Django, django CMS and other required packages
   ```
   pip install django-cms
   ```
3. Create project `<<project_name>>` using this template
   ```
   djangocms <<project_name>>
   cd <<project_name>>
   ```
4. Run testserver
   ```
   ./manage.py runserver
   ```

Note: If you run into a problem of missing dependencies, please
update `pip` using `pip install -U pip` before running the 
`djangocms` command.

# Setting up development environment

1. Clone the repository , duh! obviously!
    ```
    git clone https://github.com/zite69/Project-Phygitalist
    ```
2. Make a copy of the env.example file.
    ```
    cp env.example .env
    ```
3. Edit your system hosts file. On Linux and Mac it is: /etc/hosts. Add an entry like this:
    ```
    127.0.0.1 seller.z69.local www.z69.local
    ```
4. Edit .env and customize according to your needs. But change the following at least:
    ```
    ALLOWED_HOSTS=seller.z69.local,www.z69.local # Add the values that you added above - in the /etc/hosts file
    SECRET_KEY=# Generate some random string 32+ characters long and use here
    DEBUG=True #To enable debugging features in local development
    ZITE69_SU_USERNAME=myuser # Username for the system admin user
    ZITE69_SU_PASSWORD=mypass123 # Password for the system admin user
    ```
5. Now run the following commands one after another. Depending on the speed of the machine, this process can take upto an hour to run. Because it creates the database and loads Country and Pincode data into the database and there are over 150k rows in the Pincode table.
    ```
    python manage.py migrate
    python manage.py runscript initialize_db
    python manage.py runscript createsu
    ```
6. Now you can run the local server with:
    ```
    python manage.py runserver 0.0.0.0:8000
    ```
7. Now go to http://www.z69.local:8000/ and you will be asked to login and create the CMS page for the home page. Create that, and then do the same with http://seller.z69.local:8000/ and create that CMS page as well.

# Payment Testing
Use following credit cards for testing razorpay payment gateway - https://razorpay.com/docs/payments/payments/test-card-details/

# Email Templates
We use mjml for the email templates. mjml requires the npm mjml library and binary to be installed. Use npm 
or pnpm to install the packages needed:
`$ pnpm i`
