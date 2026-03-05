-- 更新数据查询菜单
UPDATE menus 
SET title = 'dataQuery' 
WHERE name = '数据查询' OR name = 'DataQuery';

-- 更新拆分匹配菜单
UPDATE menus 
SET title = 'splitMatch' 
WHERE name = '拆分匹配' OR name = 'SplitMatch';

-- 更新详单查询菜单
UPDATE menus 
SET title = 'detailQuery' 
WHERE name = '详单查询' OR name = 'DetailQuery';

-- 查看更新结果
SELECT id, name, title, path FROM menus WHERE title IN ('dataQuery', 'splitMatch', 'detailQuery');
