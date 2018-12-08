# Database-Project

Intro to Databases Project
Pricosha Extra Features
Nowsha Islam, David Li, Eli Zhu

1. David Li – Deleting a post
Pricosha allows the user to remove a ContentItem that they have posted. Any person who was tagged will no longer be tagged. This is a good feature because it’s very plausible a user would want to remove something they posted. Nothing additional will need to be added to the database schema. The post will simply be removed.

Application source code for the deletepost feature can be found beginning at line 225.
Queries used to implement the deletepost feature:
#checks to make sure the user does not try to delete an item they did not post by entering the item_id in the url
postsquery = 'SELECT * from contentitem 
          WHERE item_id = %s AND item_id IN (SELECT DISTINCT item_id 
    FROM contentitem 
    WHERE email_post = %s)'
cursor.execute(postsquery, (item_id, email))
# this deletes the post with the item_id specified
itemToDelete = 'DELETE FROM contentitem 
   WHERE item_id = %s'
cursor.execute(itemToDelete, (item_id))

Screenshots demonstrating the deletepost features: 

1.1 Under the Your Profile page, the user has the option to delete posts

![1](https://github.com/mobulture/Database-Project/tree/master/Screenshots/1.png)

Corresponding Data:
![2](https://github.com/mobulture/Database-Project/tree/master/Screenshots/2.png)

1.2 After deleting the “test” post, the post is no longer shown
![3](https://github.com/mobulture/Database-Project/tree/master/Screenshots/3.png)

The post is also no longer in the database:
![4](https://github.com/mobulture/Database-Project/tree/master/Screenshots/4.png)
 
2. David Li - Defriending
A user will be able to remove someone from a FriendGroup the user owns.This is a good feature because FriendGroups should be dynamic. It should be possible to remove friends in addition to adding them.  Nothing additional will need to be added to the database schema. The user will simply be removed from the FriendGroup. (posts are also removed?) (dont need to talk about mem_status here i believe, will only say if they are a member..)

Application source code  for the unfriend feature can be found beginning at line 409. 
Queries used to implement the unfriend feature:
# protects against someone entering data from url trying to delete user not in group
query = 'SELECT * FROM belong 
   WHERE email = %s AND fg_name = %s AND owner_email = %s'
 cursor.execute(query, (friend_email, fg_name, admin_email))
#this deletes from the tag table if someone who tagged or was tagged can no longer see the contentitem because of soemone being removed from a fg
deletetag = 'delete from tag where item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s) and (email_tagged in (select email from belong where fg_name = %s and owner_email = %s) and email_tagged not in (select email from belong natural join share where fg_name != %s and item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s)) or (email_tagger in (select email from belong where fg_name = %s and owner_email = %s) and email_tagger not in (select email from belong natural join share where fg_name != %s and item_id in (select item_id from belong natural join share where owner_email = %s and fg_name = %s and email = %s))))'
cursor.execute(deletetag, (admin_email, fg_name, friend_email, fg_name, admin_email, fg_name, admin_email, fg_name, friend_email, fg_name, admin_email, fg_name, admin_email, fg_name, friend_email))

 #this deletes the item from the share table
shareToDelete = 'Delete from share where owner_email = %s and fg_name = %s and item_id in (select item_id from (select item_id from belong natural join share natural join contentitem where owner_email = %s and fg_name = %s and email_post = %s) as alias )'
cursor.execute(shareToDelete, (admin_email, fg_name, admin_email, fg_name, friend_email))
        
# this removes a friend from the belong table
itemToDelete = 'DELETE FROM belong 
   WHERE email = %s AND fg_name = %s AND owner_email = %s'
cursor.execute(itemToDelete, (friend_email, fg_name, admin_email))
        
Screenshots demonstrating the unfriend feature: 
2.1 Under the Your Profile page, the user has the option to defriend a member,  thus removing them from a group.

![5](https://github.com/mobulture/Database-Project/tree/master/Screenshots/5.png)

Corresponding Data:

![6](https://github.com/mobulture/Database-Project/tree/master/Screenshots/6.png)

2.2 After removing John Doe from people, John Doe is no longer listed as a member of people. 

![7](https://github.com/mobulture/Database-Project/tree/master/Screenshots/7.png)

He is also no longer listed as a member in the database. 

![8](https://github.com/mobulture/Database-Project/tree/master/Screenshots/8.png)

 3. Eli Zhu – Member Hierarchy
 Pricosha will allow owners to promote members to be moderators of a FriendGroup. A moderator has the ability to remove members from the FriendGroup. Owners can also demote members from being moderators. This feature allows more users to have an input on who can belong to a FriendGroup. This additional feature will make users more invested in their FriendGroups. The attribute mem_status was added to Belong to indicate if a member was an admin or moderator. 
Application source code for the givemod feature can be found beginning at line 247.
Queries used to implement the givemod feature:
 #check if person exists
checkquery = 'SELECT * FROM belong 
WHERE owner_email = %s AND fg_name = %s AND email = %s'
cursor.execute(checkquery,(email,fg_name, to_mod))
#this query updates the mem_status to moderator
mod_query = "update belong set mem_status = 'moderator' where owner_email = %s and fg_name = %s and email = %s"
cursor.execute(mod_query,(email,fg_name, to_mod))
Application source code for the unmod feature can be found beginning at line 272. 
Queries used to implement the unmod feature:
#check if person exists
checkquery = 'SELECT * FROM belong 
WHERE owner_email = %s AND fg_name = %s AND email = %s'
cursor.execute(checkquery,(email,fg_name, de_mod))
#this query changed mem_status from moderator to member
mod_query = "update belong set mem_status = 'member' where owner_email = %s and fg_name = %s and email = %s" cursor.execute(mod_query,(email,fg_name, de_mod))
cursor.execute(mod_query,(email,fg_name, de_mod))

Screenshots demonstrating the givemod/unmod features: 
3.1 When a user logs in, the home page displays what groups the user owns as well as groups the user moderates. 

![9](https://github.com/mobulture/Database-Project/tree/master/Screenshots/9.png)

3.2 The owner can choose who can be a moderator in the Your Profile page

![10](https://github.com/mobulture/Database-Project/tree/master/Screenshots/10.png)

Corresponding Data:

![11] (https://github.com/mobulture/Database-Project/tree/master/Screenshots/11.png)

3.3 Data after owner demotes John Doe from being a moderator in people
![12](https://github.com/mobulture/Database-Project/tree/master/Screenshots/12.png)
 
4. Nowsha Islam – Comments
User will be able to add comments to ContentItems that are visible to them. A comments table was added to the database. The comments table contains the following attributes: comment_id, comment, comment_time, item_id, and email_comment (the email of the user who commented.) The primary key is comment_id. The attribute item_id in comments is a foreign key from comments, referencing ContentItem(item_id.)
This is a good feature because it gives Pricosha more functionality and allows the user to express their opinions on different posts.The attribute email_comment in comments is a foreign key from comments, referencing Person(email.)

Application source code for the comments feature can be found beginning at line 324
Queries used to implement the comments feature:
#check if item_id is one of the items you can see

postsquery = 'SELECT * FROM contentitem 
          WHERE item_id = %s AND item_id IN (SELECT DISTINCT item_id 							                 FROM contentitem 									     WHERE (item_id IN (SELECT item_id 						        	     FROM contentitem NATURAL JOIN 							     belong NATURAL JOIN share 								     WHERE email = %s) OR item_id IN 							     (SELECT item_id FROM contentitem 							     WHERE is_pub = true)))'
cursor.execute(postsquery, (item_id, email))
#this query returns all the comments that are already posted for a content item
getcomments = 'SELECT DISTINCT comment_id, comment, comment_time, item_id, 				  email_comment FROM comments 							
  WHERE item_id = %s'
cursor.execute(getcomments, (item_id))
#this query inserts the users comment into the comments table
ins = 'INSERT INTO comments (comment, comment_time, item_id, email_comment) 
         VALUES(%s, %s, %s, %s)'
cursor.execute(ins, (comment, time, item_id, email))

Screenshots demonstrating the comments feature: 
4.1 When the user logs in, the option to comment on other people’s posts is shown on the home page. 

![13](https://github.com/mobulture/Database-Project/tree/master/Screenshots/13.png)

4.2 Clicking on Comments will show a page that gives the option to comment on the selected ContentItem and previous comments. 

![14](https://github.com/mobulture/Database-Project/tree/master/Screenshots/14.png)
![15](https://github.com/mobulture/Database-Project/tree/master/Screenshots/15.png)

4.3 Database before the “cool” comment is posted: 

![16](https://github.com/mobulture/Database-Project/tree/master/Screenshots/16.png)

4.4 Database after the “cool” comment is posted:

![17](https://github.com/mobulture/Database-Project/tree/master/Screenshots/17.png)
