# ScheduleMe

We need a fully automated scheduler for semester-long lecture plans and also for exam situations. This project builds a minimum viable scheduler system, using industry grade optimization software and very simple design principles. We first make it work, then make it work better and then make it pretty.

## The plan

### v0

* Information needs to be stored in tables. We use Excel (!!) to simulate tables, because it's easy and enough for our prototype.
  * If v0 works out, we'll use sqlite. Or maybe something else.
  * Yes, Excel. The one that comes with the university license. Easy to type into, easy to look at, easy to change. If we find out that Excel is a stupid idea, we ditch it. We access the various excel files by downloading them and reading them in through pandas.
  * What tables do we need?
    * A table (i.e. an excel file) for every lecture that needs to happen. Let's use a handful (10 - 12) of lectures from the KI Modulehandbuch. A lecture has the following columns
      * Lecture id, use the Module id (e.g. "KI150" for "Programming in Python"). In Databases this is called our primary key. It needs to be unique.
      * Amount of 2 SWS lecture units (e.g. the row for KI150 should have 2 for this column because 4 SWS = 2 * 2SWS)
      * Amount of 2 SWS practical units (e.g. 1 for KI150 because it has 1*2 SWS practicals).
      * Participants. Use random numbers between 20 and 50.
      * Participants for practicals. Maximum number of participants per practical. Choose random number between 10 and 20.
      * Lecturer: Who is doing the lecture (and practicals). This is a **foreign key** in a database, and refers to the primary key of the 'lecturer' table
      * Anything else?
    * Rooms table (another Excel file). Let's assume there are 3 lecture rooms (J101, G018, G005) with capacities 30, 45 and 60. Also let's assume there are two rooms for practicals (K016, K012), each with a capacity of 30.
      * Room id.
      * Room capacity.
      * Anything else?
        * In later version we will imagine that each room has an availability information (see below with lecturer)
    * Lecturer table. There are 5 lecturers available, L01, L02, L03, L04, L05. Each one  should be responsible for two or three of the above lectures (reflected in the foreign key column).
      * Lecture id. The primary key.
      * Availability (the crux): There are 10 45 minutes slots on a day (starting from 8:45 in the morning), there are 5 days per week, so this should be 50 columns. I'd suggest to name the first 10 columns M0, M1, ..., M9 (M for Monday), then T0 (Tuesday), ..., and W0 (for Wednesday), ... and D0 (for Thursday!!) and F0, ... for Friday. These are binary entries, meaning the lecture could use this slot for one of their lecture or not. Fill these more or less randomly for each lecturer: Eeach person should have one day completely blocked (i.e. not available), and for the remaining days either one or two slots at the very beginning or at the very end of every day should be blocked, with two or three slots in total blocked in between.
        * This whole idea depends on the actual scheduling tool. If this suggestion is stupid, fix it with a better approach that matches the tool.

* Scheduling: https://github.com/google/or-tools. If there is a better suited open source tool, we will use it instead.

* Approach:
  * Let's use python. import statements are allowed.
  * Build the data base first, this shouldn't be more than a couple of hours max.
  * Check out the tool, find closest examples, play around with toys.
  * Iterate the data in, iterate over your understanding.
    * Apart from the availability question there probably lurk a few tricky questions. For example, if there are 56 participants, and practicals can have 17 participants each, how is this handled properly?
  * The goal is to have very rudementary code base that can solve the above scheduling task under all constraints. If this is not possible (i.e. the goal can't be met) it's important to understand all aspects that make this task unsolvable, and potentially how the problem setting needs to be changed to get a feasable solution.
