import sqlite3
import json
import base64
import argparse
import os
import sys

def db_to_json(db_path, json_path):
    """
    将 SQLite 数据库无损转换为 JSON 格式
    
    参数:
        db_path (str): SQLite 数据库文件路径
        json_path (str): 输出的 JSON 文件路径
    """
    try:
        # 验证输入文件是否存在
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"数据库文件不存在: {db_path}")
            
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 支持列名访问
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("警告: 数据库中没有找到任何表")
        
        db_json = {
            "metadata": {
                "source_db": os.path.basename(db_path),
                "tables_count": len(tables),
                "conversion_timestamp": conn.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', 'now')").fetchone()[0]
            },
            "tables": {}
        }

        for table in tables:
            # 1. 获取表结构元数据
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            schema = []
            for col in columns:
                schema.append({
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                })
            
            # 2. 获取主键信息
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = cursor.fetchall()
            primary_keys = []
            for idx in indexes:
                if idx[1].startswith('sqlite_autoindex'):
                    cursor.execute(f"PRAGMA index_info({idx[1]})")
                    pk_info = cursor.fetchall()
                    primary_keys = [col[2] for col in pk_info]
            
            # 3. 获取表数据
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data = []
            for row in rows:
                row_dict = {}
                for col_name in row.keys():
                    value = row[col_name]
                    
                    # 处理特殊数据类型
                    if isinstance(value, bytes):
                        # BLOB 类型转为 Base64
                        value = base64.b64encode(value).decode('utf-8')
                    elif value is None:
                        # 保留 NULL 值
                        value = None
                    row_dict[col_name] = value
                data.append(row_dict)
            
            # 4. 合并元数据与数据
            db_json["tables"][table] = {
                "schema": schema,
                "primary_keys": primary_keys,
                "row_count": len(data),
                "data": data
            }

        # 5. 导出为 JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(db_json, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 转换成功! 共转换 {len(tables)} 张表")
        print(f"📁 JSON 文件已保存至: {os.path.abspath(json_path)}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='将 SQLite 数据库无损转换为 JSON 格式')
    parser.add_argument('input_db', help='输入的 SQLite 数据库文件路径 (.db)')
    parser.add_argument('output_json', nargs='?', default=None, 
                        help='输出的 JSON 文件路径 (默认: [数据库名].json)')
    
    args = parser.parse_args()
    
    # 处理输出文件名
    if not args.output_json:
        base_name = os.path.splitext(os.path.basename(args.input_db))[0]
        args.output_json = f"{base_name}.json"
    
    # 检查输出文件是否已存在
    if os.path.exists(args.output_json):
        response = input(f"⚠️ 文件 {args.output_json} 已存在，是否覆盖? (y/n): ")
        if response.lower() != 'y':
            print("操作已取消")
            sys.exit(0)
    
    # 执行转换
    success = db_to_json(args.input_db, args.output_json)
    
    if not success:
        sys.exit(1)