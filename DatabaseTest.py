from flask import Flask, flash, render_template, request, session, url_for, redirect
import pymysql.cursors
import datetime
from datetime import timedelta
import hashlib

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@app.route('/')
def hello():
    cursor = conn.cursor()
    #this gets the data for the 24hour public posts on the landing page
    #this calculates the datetime of 24 hours ago
    cutoff_time = (datetime.datetime.now()) - (timedelta(hours=24))
    #this query looks for all contentitems that are public and posted after the cutoff time
    publicquery = 'SELECT item_id, email_post, post_time, file_path, item_name FROM contentitem WHERE is_pub = true and post_time > %s ORDER BY post_time DESC'
    cursor.execute(publicquery, (cutoff_time))
    publicdata = cursor.fetchall()
    cursor.close()
    return render_template('index.html', publicposts=publicdata)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    #print(password)    
    h = hashlib.sha256(password.encode()).hexdigest()
    #toprint = h.hexdigest
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s and password = %s'
    cursor.execute(query, (email, h))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['email'] = email
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or email'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    email = request.form['email']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    #print(password)    
    h = hashlib.sha256(password.encode()).hexdigest()
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE email = %s'
    cursor.execute(query, (email))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (email, h, fname, lname))
        conn.commit()
        cursor.close()
        return redirect('/') 


@app.route('/home')
def home():
    user = session['email']
    cursor = conn.cursor();
    #this query chooses all the posts the current user can see
    postsquery = 'SELECT DISTINCT item_id, email_post, post_time, file_path, item_name FROM contentitem where email_post != %s and (item_id in (Select item_id from contentitem natural join belong natural join share where email = %s) or item_id in (select item_id FROM contentitem WHERE is_pub = true)) ORDER BY post_time DESC'
    cursor.execute(postsquery, (user, user))
    postsdata = cursor.fetchall()
    #this query selects all the friendgroups the user owns to be able to add people to
    ownsquery = 'SELECT distinct owner_email, fg_name FROM belong WHERE owner_email = %s ORDER BY fg_name ASC'
    cursor.execute(ownsquery, (user))
    ownsdata = cursor.fetchall()    
    #this query selects all the fgs that the user is a moderator of (extra feature)
    modquery = "Select distinct owner_email, fg_name from belong where email =%s and mem_status = 'moderator'"
    cursor.execute(modquery,(user))
    moddata =cursor.fetchall()
    cursor.close()
    return render_template('home.html', email=user, posts=postsdata, owns=ownsdata, moddata=moddata)

#this page allows the user to see all the posts they made and their friends
@app.route('/profile')
def profile():
    user = session['email']
    cursor = conn.cursor();
    #this query selects all the posts that they made
    postsquery = 'SELECT DISTINCT item_id, email_post, post_time, file_path, item_name FROM contentitem where email_post = %s ORDER BY post_time DESC'
    cursor.execute(postsquery, (user))
    postsdata = cursor.fetchall()
    #this query selects all the friends the user has in their friendgroups
    friendsquery = 'SELECT email, fname, lname, fg_name, owner_email, mem_status FROM belong natural join person WHERE owner_email = %s and email != %s ORDER BY fname, lname DESC'
    cursor.execute(friendsquery, (user, user))
    friendsdata = cursor.fetchall()    
    #this query selects members of friendsgroups that you moderate
    modquery = 'select email,fname,lname,fg_name,owner_email,mem_status from belong natural join person where mem_status = "member" and fg_name in (Select fg_name from (select fg_name from belong where email = %s and mem_status = "moderator") as modgroups)'
    cursor.execute(modquery, (user))
    moddata = cursor.fetchall()
    cursor.close()
    return render_template('profile.html', email=user, posts=postsdata, groups=friendsdata, moddata=moddata)

#this function creates friendgroups
@app.route('/createfriendgroup', methods=['GET', 'POST'])
def createfriendgroup():
    email = session['email']
    cursor = conn.cursor();
    fg_name = request.form['fg_name']
    description = request.form['description']
    #this checks to make sure the user does not already have a fg of the same name
    query = 'SELECT * from friendgroup where owner_email = %s and fg_name = %s'
    cursor.execute(query, (email, fg_name))
    data = cursor.fetchone()
    if (data):
        #if the fg already exists display an error
        cursor.close()
        flash('You have already created such a friendgroup')
        return redirect(url_for('home'))
    else:
        #else create the fg and add the current user in the belong table as belonging to own group
        ins = 'INSERT INTO friendgroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (email, fg_name, description))
        conn.commit()
        belongins = 'INSERT INTO belong VALUES(%s, %s, %s,"admin")'
        cursor.execute(belongins, (email, email, fg_name))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#this allows users to post
@app.route('/post', methods=['GET', 'POST'])
def post():
    email = session['email']
    cursor = conn.cursor();
    item_name = request.form['item_name']
    item_link = request.form['item_link']
    is_public_form = request.form['is_public']
    if is_public_form == 'true':
        is_pub = True
    else:
        is_pub = False
    time = datetime.datetime.now()
    ins = 'INSERT INTO contentitem (email_post, post_time, file_path, item_name, is_pub) VALUES(%s, %s, %s, %s, %s)'
    cursor.execute(ins, (email, time, item_link, item_name, is_pub))
    
    conn.commit()
    cursor.close()
    #if the user selected private they are directed to a different page to complete the process
    if is_pub == False:
        return redirect(url_for('contentitem'))
    else:
        return redirect(url_for('home')) 
 
#this page is where users choose fgs to post in if they select their post as private
@app.route('/contentitem')
def contentitem():
    email = session['email']
    cursor = conn.cursor();
    #this query selects all of the friendgroups the user is a part of
    groupsquery = 'SELECT fg_name, owner_email FROM belong WHERE email = %s ORDER BY fg_name ASC'
    cursor.execute(groupsquery, (email))
    groupsdata = cursor.fetchall()
    cursor.close()
    return render_template('contentitem.html', email=email, groups=groupsdata)

#this function assigns a contentitem to friendgroup(s) the user belongs to
@app.route('/assignfg', methods=['GET', 'POST'])
def assignfg():
    #gets all the selected groups. The form on the page gives fg name and onwer of that fg
    groups = request.form.getlist('groupassign')
    #this query chooses the item_id of the last item created which is the one we just created
    cursor = conn.cursor();
    #this function comes after an item was created so to insert to share we take the max of item_id    
    last_num_query = 'SELECT MAX(item_id) as last from contentitem'
    cursor.execute(last_num_query)
    elem = cursor.fetchone()
    last_num = elem["last"]
    #for each of the groups selected
    for values in groups:    
        params = values.split('/',)
        fg_name = params[0]
        owner_email = params[1]        
        #this query inserts
        ins = 'INSERT INTO share VALUES(%s, %s, %s)'
        cursor.execute(ins, (owner_email, fg_name, last_num))
    cursor.close()
    return redirect(url_for('home'))

#this function is used to delete a post (extra feature)
@app.route('/deletepost', methods=['GET', 'POST'])
def deletepost():    
    email = session['email']
    #this grabs the item_id from the url supplied from the page
    item_id = request.args.get('item_id')
    cursor = conn.cursor();
    #checks to make sure the user does not try to delete an item they did not post by entering the item_id in the url
    postsquery = 'select * from contentitem where item_id = %s and item_id in (SELECT DISTINCT item_id FROM contentitem where email_post = %s)'
    cursor.execute(postsquery, (item_id, email))
    postcheck = cursor.fetchone()
    if (postcheck):
        #this deletes the post with the item_id we specified
        itemToDelete = 'DELETE FROM contentitem where item_id = %s'
        cursor.execute(itemToDelete, (item_id))
        conn.commit()
        cursor.close()
        return redirect(url_for('profile'))
    else:
        flash("You are not allowed to delete that contentitem. It is not one of yours")
        return redirect(url_for('profile'))

#this function is used to give someone moderator status in a specific fg (extra feature)
@app.route('/givemod', methods = ['GET','POST'])
def givemod():
    email = session['email']
    cursor =conn.cursor()
    to_mod = request.args.get('to_mod')
    fg_name = request.args.get('fg_name')
    #check if person exists
    checkquery = 'select * from belong where owner_email = %s and fg_name = %s and email = %s'
    cursor.execute(checkquery,(email,fg_name, to_mod))
    ingroup = cursor.fetchone()
    if not ingroup:
        flash("That person is not in the group")
        return redirect(url_for('profile'))
    #check if the person is the owner (admin) of the fg
    if not auth_admin(email,fg_name):
        flash ("You do not own this friendgroup")
        return redirect(url_for('profile'))
    #changes the mem_status in belong so that it is now moderator
    mod_query = "update belong set mem_status = 'moderator' where owner_email = %s and fg_name = %s and email = %s"
    cursor.execute(mod_query,(email,fg_name, to_mod))
    conn.commit()
    cursor.close()
    return redirect(url_for('profile'))
    
#this function is used to remove someone's moderator status in a specific fg (extra feature)
@app.route('/unmod', methods = ['GET','POST'])
def unmod():
    email = session['email']
    cursor =conn.cursor()
    de_mod = request.args.get('de_mod')
    fg_name = request.args.get('fg_name')
    #check if person exists
    checkquery = 'select * from belong where owner_email = %s and fg_name = %s and email = %s'
    cursor.execute(checkquery,(email,fg_name, de_mod))
    exists = cursor.fetchone()
    if not exists:
        flash("That person is not in the group")
        return redirect(url_for('profile'))
    #check if the person is the owner (admin) of the fg
    if not auth_admin(email,fg_name):
        #if not then don't change anything and present error
        flash ("You do not own this friendgroup")
        return redirect(url_for('profile'))
    #changes the mem_status in belong so that it is no longer moderator
    mod_query = "update belong set mem_status = 'member' where owner_email = %s and fg_name = %s and email = %s"
    cursor.execute(mod_query,(email,fg_name, de_mod))
    conn.commit()
    cursor.close()
    return redirect(url_for('profile'))

#this function checks if the user is a moderator or admin of the friendgroup (extra feature related)
def authorize(admin_email, email, fg_name):
    cursor = conn.cursor()
    status_query = "Select mem_status from belong where owner_email = %s and email = %s and fg_name = %s"
    cursor.execute(status_query,(admin_email, email, fg_name))
    auth = cursor.fetchone()
    cursor.close()
    status = auth['mem_status']
    if (status == "moderator" or status == "admin"):
        return True
    else:
        return False

# this function checks if the user is an owner/admin of the friendgroup (extra feature related)
def auth_admin(owner_email, fg_name):
    cursor = conn.cursor()
    status_query = "Select mem_status from belong where owner_email = %s and fg_name =%s"
    cursor.execute(status_query, (owner_email, fg_name))
    auth = cursor.fetchone() 
    status = auth['mem_status']
    cursor.close()
    if (status == "admin"):
        return True
    else:
        return False

#page displaying comments and where users can add comments (extra feature)
@app.route('/comment')
def comment():
    email = session['email']
    item_id = request.args.get('item_id')
    cursor = conn.cursor();
    #check if item_id is one of the items the user can see
    postsquery = 'select * from contentitem where item_id = %s and item_id in (SELECT DISTINCT item_id FROM contentitem where (item_id in (Select item_id from contentitem natural join belong natural join share where email = %s) or item_id in (select item_id FROM contentitem WHERE is_pub = true)))'
    cursor.execute(postsquery, (item_id, email))
    data = cursor.fetchone()
    if (data):
        getcomments = 'SELECT DISTINCT comment_id, comment, comment_time, item_id, email_comment FROM comments WHERE item_id = %s'
        cursor.execute(getcomments, (item_id))
        othercomments = cursor.fetchall()
        cursor.close()
        return render_template('comments.html', item_id=item_id, othercomments=othercomments)
    else:
        flash('You do not have permission to see this contentitem')
        return redirect(url_for('home'))
        
#function that allows for adding comments (extra feature)
@app.route('/givecomment', methods=['GET', 'POST'])
def givecomment():
    email = session['email']
    time = datetime.datetime.now()
    cursor = conn.cursor();
    comment = request.form['comment']
    item_id = request.form['item_id']
    ins = 'INSERT INTO comments (comment, comment_time, item_id, email_comment) VALUES(%s, %s, %s, %s)'
    cursor.execute(ins, (comment, time, item_id, email))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#this function allows the user to add people to friendgroups the user owns
@app.route('/addfriend', methods=['GET', 'POST'])
def addfriend():
    email = session['email']
    cursor = conn.cursor();
    fname = request.form['fname']
    lname = request.form['lname']
    #this param is returning group name and the owner of that group
    params = request.form['owngroups']
    params_array = params.split('/',)
    fg_name = params_array[0]
    admin_email = params_array[1]
    #checks to make sure the user is a mod or admin so they can add to the fg
    adminormod = authorize(admin_email, email,fg_name)
    if (adminormod == False):
        flash("You do not have the authority for this action")
        return redirect(url_for('home'))
    #this returns the number of people with the specified name
    query = 'SELECT count(email) AS total FROM person WHERE fname = %s and lname = %s'
    cursor.execute(query, (fname, lname))
    elem = cursor.fetchone()
    count = elem["total"]
    #if there is one person with that name, add that person to the fg
    if count == 1:
        query = 'SELECT email FROM person WHERE fname = %s and lname = %s'
        cursor.execute(query, (fname, lname))
        toAdd = cursor.fetchone()
        friendemail = toAdd["email"]
        #this makes sure that one person doesn't already belong to that fg
        query = 'Select * from belong where fg_name = %s and email = %s and owner_email = %s'
        cursor.execute(query, (fg_name, friendemail, admin_email))
        data = cursor.fetchone()        
        if(data):
            flash('That person is already in the friendgroup')
            return redirect(url_for('home'))
        else:
            belongins = 'INSERT INTO belong VALUES(%s, %s, %s,"member")'
            cursor.execute(belongins, (friendemail, admin_email, fg_name))
            conn.commit()
            return redirect(url_for('home'))
    #if the person doesn't exist display this message
    elif count == 0:
        flash('That person does not exist')
        return redirect(url_for('home'))
    #if there are multiple people with that name continue the process on a different page
    elif count > 1:
        query = 'SELECT fname, lname, email FROM person WHERE fname = %s and lname = %s'
        cursor.execute(query, (fname, lname))
        people = cursor.fetchall()
        return render_template('verifyfriend.html', people=people, fg_name=fg_name, admin_email=admin_email)

#this function is used to remove friends from friendgroup (extra feature)
@app.route('/unfriend', methods=['GET', 'POST'])
def unfriend():
    email = session['email']
    friend_email = request.args.get('friend_email')
    fg_name = request.args.get('fg_name')
    admin_email = request.args.get('owner_email')
    #this protects from a user is trying to change friends through the url
    #this checks if the user that is logged in has mod or admin status in the fg
    if (authorize( admin_email, email, fg_name ) == False):
        flash("You do not have permission for this task")
        return redirect(url_for('profile'))
    cursor = conn.cursor();
    #protects against someone entering data from url trying to delete user not in group
    query = 'Select * FROM belong where email = %s and fg_name = %s and owner_email = %s'
    cursor.execute(query, (friend_email, fg_name, admin_email))
    ingroup = cursor.fetchone()
    if (ingroup):

        #this deletes from the tag table if someone who tagged or was tagged can no longer see the contentitem because of soemone being removed from a fg
        deletetag = 'delete from tag where item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s) and (email_tagged in (select email from belong where fg_name = %s and owner_email = %s) and email_tagged not in (select email from belong natural join share where fg_name != %s and item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s)) or (email_tagger in (select email from belong where fg_name = %s and owner_email = %s) and email_tagger not in (select email from belong natural join share where fg_name != %s and item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s))))'
        cursor.execute(deletetag, (admin_email, fg_name, friend_email, fg_name, admin_email, fg_name, admin_email, fg_name, friend_email, fg_name, admin_email, fg_name, admin_email, fg_name, friend_email))
        conn.commit()          

        '''
        deleterate = 'delete from rate where item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s) and (email in (select email from belong where fg_name = %s and owner_email = %s) and email not in (select email from belong natural join share where fg_name != %s and item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s)))'
        cursor.execute(deleterate, (admin_email, fg_name, friend_email, fg_name, admin_email, fg_name, admin_email, fg_name, friend_email))
        conn.commit()

        deletecomment = 'delete from comments where item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s) and (email_comment in (select email from belong where fg_name = %s and owner_email = %s) and email_comment not in (select email from belong natural join share where fg_name != %s and item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s)))'
        cursor.execute(deletecomment, (admin_email, fg_name, friend_email, fg_name, admin_email, fg_name, admin_email, fg_name, friend_email))
        conn.commit()        
        '''
        
        #this deletes the item from the share table
        shareToDelete = 'Delete from share where owner_email = %s and fg_name = %s and item_id in (select item_id from (select item_id from belong natural join share natural join contentitem where owner_email = %s and fg_name = %s and email_post = %s) as alias )'
        cursor.execute(shareToDelete, (admin_email, fg_name, admin_email, fg_name, friend_email))
        conn.commit()  
        
        #this removes a friend from the belong table
        itemToDelete = 'DELETE FROM belong where email = %s and fg_name = %s and owner_email = %s'
        cursor.execute(itemToDelete, (friend_email, fg_name, admin_email))
        conn.commit()

        #this removes the contentitem if no user can see it anymore
        notseen = 'delete from contentitem where item_id not in (select distinct item_id from contentitem where item_id in (select item_id from contentitem natural join belong natural join share)) and item_id not in (select DISTINCT item_id from contentitem where is_pub = true)'
        cursor.execute(notseen)
        conn.commit
        
        
        cursor.close()
        return redirect(url_for('profile'))
    else:
        flash("That person is not in the group")
        return redirect(url_for('profile'))

#on this page the user specifies which friend they wanted to add
#when there are multiple people with the same name
@app.route('/verifyfriend')
def verifyfriend():
    return render_template('verifyfriend.html')

#after specifying the friend we run this function which adds the friend to the group
@app.route('/confirmfriend', methods=['GET', 'POST'])
def confirmfriend():
    cursor = conn.cursor();
    friendemail = request.form['verifyemail']
    fg_name = request.form['fg_name']
    admin_email = request.form['admin_email']
    #makes sure the person selected is not already in the fg
    query = 'Select * from belong where fg_name = %s and email = %s and owner_email = %s'
    cursor.execute(query, (fg_name, friendemail, admin_email))
    data = cursor.fetchone()     
    #if they are already in the fg, display this error
    if(data):
        flash('That person is already in the friendgroup')
        return redirect(url_for('home'))
    #if not, add them
    else:
        belongins = 'INSERT INTO belong VALUES(%s, %s, %s,"member")'
        cursor.execute(belongins, (friendemail, admin_email, fg_name))
        conn.commit()
        return redirect(url_for('home'))

#this page is where the user manages their tags
@app.route('/tag')
def tag():
    email = session['email']
    cursor=conn.cursor();
    #this is the query for all the tags they have pending their approval
    tag_query = 'select email_tagged, email_tagger, item_id, status, tagtime from tag where email_tagged = %s and status = True'
    cursor.execute(tag_query ,(email))
    current_tags =  cursor.fetchall()
    #this is the query for all the tags they have approved of
    tag_query = 'select email_tagged, email_tagger, item_id, status, tagtime from tag where email_tagged = %s and status = False'
    cursor.execute(tag_query ,(email))
    pending_tags =  cursor.fetchall()
    cursor.close()
    return render_template('tag.html', current_tags=current_tags, pending_tags=pending_tags)

#this function allows the user to accept or decline tags
@app.route('/tag_valid', methods=['GET','POST'])
def tag_valid():
    email_tagger=request.args.get('email_tagger')
    item_id = request.args.get('item_id')
    acceptance = request.args.get('acceptance')
    email_tagged = session['email']
    cursor=conn.cursor();
    if (acceptance == "true"):
        validate = "Update tag set status = True where email_tagged = %s and item_id = %s and email_tagger = %s"
    else:
        validate = "delete from tag where email_tagged = %s and item_id = %s and email_tagger = %s"
    cursor.execute(validate, (email_tagged, item_id, email_tagger))
    cursor.close()
    return redirect(url_for('tag'))

#on this page users specify who they will be tagging
@app.route('/tagging')
def tagging():
    email = session['email']
    item_id = request.args.get('item_id')
    cursor=conn.cursor();
    #this query checks if the user has permission to see this contentitem
    postsquery = 'select * from contentitem where item_id = %s and item_id in (SELECT DISTINCT item_id FROM contentitem where (item_id in (Select item_id from contentitem natural join belong natural join share where email = %s) or item_id in (select item_id FROM contentitem WHERE is_pub = true)))'
    cursor.execute(postsquery, (item_id, email))
    data = cursor.fetchone()       
    if (data):
        return render_template('tagging.html', item_id=item_id)
    else:
        flash('You do not have permission to see this item')
        return redirect(url_for('home'))

#this function creates the tag from the user
@app.route('/tagperson', methods=['GET','POST'])
def tagperson():
    email = session['email']
    time = datetime.datetime.now()
    item_id = request.form['item_id']
    cursor = conn.cursor();
    taggee_email = request.form['taggee_email']
    #checks if person exists
    checkquery = 'select * from person where email = %s'
    cursor.execute(checkquery, (taggee_email))
    personcheck = cursor.fetchone() 
    if not personcheck:
        flash('That person does not exist')
        return redirect(url_for('home'))       
    #check if the contentitem is viewable to the person
    query = 'SELECT * FROM contentitem where item_id = %s and (item_id in (Select item_id from contentitem natural join belong natural join share where email = %s) or item_id in (select item_id FROM contentitem WHERE is_pub = true))'
    cursor.execute(query, (item_id, taggee_email))
    data = cursor.fetchone()
    if not data:
        flash('That person cannot view that post')
        return redirect(url_for('home'))
    #sets status based on self tagging or not
    if (taggee_email == email):
        status = True
    else:
        status = False
    #check if a tag with that item_id, email_tagged, and email_taggee already exists because it is pk of tag
    exist_query = 'Select * from tag where item_id = %s and email_tagged = %s and email_tagger = %s'
    cursor.execute(exist_query, (item_id, taggee_email, email))
    exist_data = cursor.fetchone()
    if (exist_data):
        cursor.close()
        flash('You have already made that tag')
        return redirect(url_for('home'))
    else:
        query = 'INSERT into tag values(%s, %s, %s, %s, %s)'
        cursor.execute(query, (taggee_email, email, item_id, status, time))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

#this page is where the user rates an item
@app.route('/rate')
def rate():
    email = session['email']
    item_id = request.args.get('item_id')
    cursor=conn.cursor();
    #check if the contentitem is viewable to the person
    postsquery = 'select * from contentitem where item_id = %s and item_id in (SELECT DISTINCT item_id FROM contentitem where (item_id in (Select item_id from contentitem natural join belong natural join share where email = %s) or item_id in (select item_id FROM contentitem WHERE is_pub = true)))'
    cursor.execute(postsquery, (item_id, email))
    data = cursor.fetchone()
    if (data):
        return render_template('rate.html', item_id=item_id)
    else:
        flash('You do not have permission to see this item')
        return redirect(url_for('home'))

#this function allows the user to rate an item 
@app.route('/giverating', methods=['GET','POST'])
def giverating():
    email = session['email']
    time = datetime.datetime.now()
    cursor = conn.cursor();
    rating = request.form['rating']
    item_id = request.form['item_id']
    query = 'Select * from rate where email = %s and item_id = %s'
    cursor.execute(query, (email, item_id))
    data = cursor.fetchone()
    #since email and item_id are pk but users can rate mutiple times,
    #we will allow the user to update their existing rating
    if (data):
        validate = "Update rate set emoji = %s, rate_time = %s where email = %s and item_id = %s"
        cursor.execute(validate, (rating, time, email, item_id))
    else:
        validate = "insert into rate values(%s, %s, %s, %s)"
        cursor.execute(validate, (email, item_id, time, rating))
    cursor.close()
    return redirect(url_for('home'))

#this page is where users see "more" info for a specific contentitem
@app.route('/more')
def more():
    email = session['email']
    item_id = request.args.get('item_id')
    cursor=conn.cursor();
    #check if the contentitem is viewable to the person
    postsquery = 'select * from contentitem where item_id = %s and item_id in (SELECT DISTINCT item_id FROM contentitem where (item_id in (Select item_id from contentitem natural join belong natural join share where email = %s) or item_id in (select item_id FROM contentitem WHERE is_pub = true)))'
    cursor.execute(postsquery, (item_id, email))
    data = cursor.fetchone()
    if (data):
        query = 'select fname, lname from person join tag on (person.email = tag.email_tagged) where item_id = %s and status = True'
        cursor.execute(query, (item_id))
        tags = cursor.fetchall()
        query = 'Select emoji from rate where item_id =%s'
        cursor.execute(query, (item_id))
        ratings = cursor.fetchall()
        return render_template('more.html', tags=tags, ratings=ratings)  
    else:
        flash('You do not have permission to see this item')
        return redirect(url_for('home'))
    
@app.route('/logout')
def logout():
    session.pop('email')
    return redirect('/')      
        
app.secret_key = 'a3c'

if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = False)


