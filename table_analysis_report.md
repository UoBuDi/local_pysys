# 数据库表分析报告

## 1. 表结构详情

### 1.1 gbupload_etctu_as_2024-05 表

**核心字段说明**：
- **hourBatchNo**：小时批次号，varchar(40)，非空，用于标识同一批次的数据
- **transTime**：交易时间，datetime，主键，车辆通过ETC门架的时间
- **vehiclePlate**：车牌号，varchar(40)，非空，车辆唯一标识
- **gantryId**：门架ID，varchar(40)，用于标识具体的ETC门架
- **fee**：费用，bigint，ETC交易费用信息

**索引信息**：
- 主键：(transTime, dataId)
- 普通索引：gantryId, CREATETIME
- 自增字段：dataId

### 1.2 gbupload_viu 表

**核心字段说明**：
- **hourBatchNo**：小时批次号，varchar(100)，非空，与ETC表批次号对应
- **picTime**：图片时间，datetime，主键，车辆被拍照的时间
- **vehiclePlate**：车牌号，varchar(100)，非空，车辆唯一标识
- **gantryId**：门架ID，varchar(100)，用于标识拍摄图片的门架
- **vehicleSpeed**：车辆速度，int，车辆通过时的速度信息

**索引信息**：
- 主键：(picTime, dataId)
- 普通索引：gantryId, CREATETIME
- 自增字段：dataId

## 2. 数据分布特性

| 表名 | 总数据量 | 空值情况 | 唯一值数量 |
|------|----------|----------|------------|
| gbupload_etctu_as_2024-05 | 1,623,511 | 关键字段无空值 | hourBatchNo: 743<br>vehiclePlate: 296,098 |
| gbupload_viu | 96,424,522 | 关键字段无空值 | hourBatchNo: 17,293<br>vehiclePlate: 6,084,500 |

## 3. 数据质量评估

### 3.1 异常值检测
- **空值情况**：两张表的关键关联字段（hourBatchNo、vehiclePlate、transTime/picTime）均无空值，数据完整性良好
- **数据类型匹配**：hourBatchNo在两张表中均为字符串类型，vehiclePlate也是字符串类型，便于直接关联
- **时间字段**：均为datetime类型，格式统一

### 3.2 数据一致性检查
- **hourBatchNo一致性**：两张表共有743个相同的hourBatchNo，匹配率100%
- **vehiclePlate格式**：均为车牌号字符串，格式一致

## 4. 表关联分析

### 4.1 关联逻辑

**主要关联字段**：
- **hourBatchNo**：小时批次号，用于将同一时间批次的数据关联
- **vehiclePlate**：车牌号，用于标识具体车辆
- **时间字段**：transTime（ETC交易时间）和picTime（图片拍摄时间）可用于进一步精确匹配

**关联规则**：
1. 首先通过hourBatchNo进行粗粒度关联，确保数据属于同一时间批次
2. 然后通过vehiclePlate进行车辆级别的精确关联
3. 最后可通过时间差（transTime与picTime的差值）进行最终验证

### 4.2 关联匹配率

| 统计项 | 数值 | 说明 |
|--------|------|------|
| ETC表组合键数量 | 710,138 | (hourBatchNo + vehiclePlate) 唯一组合数 |
| VIU表组合键数量 | 535,370 | (hourBatchNo + vehiclePlate) 唯一组合数 |
| 匹配的组合键数量 | 535,370 | 两张表中共同存在的组合数 |
| 匹配率 | 75.4% | ETC表中75.4%的记录可以与VIU表关联 |

### 4.3 关联限制条件

1. **时间范围限制**：建议限制时间差在合理范围内（如30秒内），避免错误关联
2. **数据量差异**：VIU表数据量远大于ETC表，需注意查询性能
3. **索引使用**：确保关联字段有合适的索引，提高查询效率

## 5. 优化的关联SQL查询

### 5.1 基础关联查询

```sql
SELECT 
    ev.*,  -- ETC交易数据
    v.*    -- 车辆图片数据
FROM 
    branchdb.`gbupload_etctu_as_2024-05` ev
INNER JOIN 
    branchdb.`gbupload_viu` v 
ON 
    ev.hourBatchNo = v.hourBatchNo
    AND ev.vehiclePlate = v.vehiclePlate
    AND ABS(TIMESTAMPDIFF(SECOND, ev.transTime, v.picTime)) <= 30  -- 时间差限制在30秒内
WHERE 
    ev.hourBatchNo = '特定批次号'  -- 可根据实际需求添加筛选条件
    AND ev.vehiclePlate = '特定车牌号';
```

### 5.2 带统计分析的关联查询

```sql
SELECT 
    ev.hourBatchNo,
    ev.vehiclePlate,
    ev.transTime,
    v.picTime,
    TIMESTAMPDIFF(SECOND, ev.transTime, v.picTime) AS time_diff,
    ev.gantryId AS etc_gantry,
    v.gantryId AS viu_gantry,
    ev.fee,
    v.vehicleSpeed
FROM 
    branchdb.`gbupload_etctu_as_2024-05` ev
INNER JOIN 
    branchdb.`gbupload_viu` v 
ON 
    ev.hourBatchNo = v.hourBatchNo
    AND ev.vehiclePlate = v.vehiclePlate
WHERE 
    ev.transTime BETWEEN '2024-05-01 00:00:00' AND '2024-05-02 00:00:00'
ORDER BY 
    ev.transTime;
```

### 5.3 优化建议

1. **添加联合索引**：
   ```sql
   -- 在gbupload_etctu_as_2024-05表上添加
   CREATE INDEX idx_hourplate ON branchdb.`gbupload_etctu_as_2024-05` (hourBatchNo, vehiclePlate, transTime);
   
   -- 在gbupload_viu表上添加
   CREATE INDEX idx_hourplate_time ON branchdb.`gbupload_viu` (hourBatchNo, vehiclePlate, picTime);
   ```

2. **分区查询**：针对大数据量的gbupload_viu表，可考虑按时间或hourBatchNo进行分区查询

3. **批量处理**：避免一次性查询全量数据，可按hourBatchNo分批处理

## 6. 结论

1. **关联可行性**：两张表具备良好的关联基础，通过hourBatchNo和vehiclePlate字段可以实现高效关联
2. **数据质量**：关键字段无空值，数据完整性良好，适合进行关联分析
3. **关联价值**：关联后可以同时获得车辆的ETC交易信息和图片信息，为数据分析提供更丰富的维度
4. **性能考虑**：由于gbupload_viu表数据量巨大，建议添加适当索引并采用分批处理方式

## 7. 潜在应用场景

- **车辆轨迹还原**：结合ETC交易时间和图片时间，还原车辆行驶轨迹
- **收费核查**：通过图片信息验证ETC收费的准确性
- **车辆识别验证**：对比ETC车辆信息与图片识别结果，提高识别准确率
- **交通流量分析**：结合门架数据和图片数据，进行更精确的交通流量统计