
select *
from fitness
ORDER BY Date;

select *
from fitness
where date > date('2015-01-01');

select *
from fitness
where Calories ISNULL
  and Date  > date('2015-09-16');

select *
from fitness
where Steps < 1
  and Date  > date('2015-09-16');

select *
from fitness
where Steps < 1
  and Date  < date('2015-09-16');