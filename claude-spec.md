**vision** : create student course management website (as single page application possible).
**requirements**
-roles - students, admin
-admin can create course
--course can have title, description, content in rich text box editor
--course can multiple attachements
--each course attachment can have label to it.
--show course attachment in tab on course
--attachements can be pdf or audio file
--when attachement is clicked, it should open embedded viewer (not download) to system
--course can deleted only by admin
--course can assigned , remove assignment to students enrolled.
-admin can have admin portal 
--student portal allows admin to create students and logins and passwords
--admin can have various settings like portal-closed, enable-chat features controlled in admin portal.
-student can see the courses assigned.
-student should be able to login with username/email assigned.
**implementation plan**
React JS with Turso/libSQL as database (no backend server required)
Single Page Application Possible 
Vercel deployment friendly
TURSO LIB CREDENTIALS - should go to env file
-attachements should go to VERCEL BLOB
VERCEL BLOB Credentials

