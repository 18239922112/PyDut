# -*- coding: utf-8 -*-
"""
@Time ： 2025/5/23 14:53
@Auth ： 七月
@File ：main.py
@IDE ：PyCharm

"""
import ast
import os
import configparser
import pymysql
import yaml
from pymysql import Error
from typing import Set


class DatabaseMigrator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, 'conf', 'db.conf')
        self.db_config = self._load_config(self.config_path)
        self.versions = self.db_config['versions']['version']
        self.conn = None
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        return config

    def _load_yaml_changes(self, filename: str =  None):
        """加载 YAML 格式的变更脚本"""
        if filename is None:
            #未指定文件获取所有文件
            dir_path = os.path.join(self.base_dir, 'sql_scripts')
            # 获取所有 .yaml 文件，并按文件名排序
            files = [f for f in os.listdir(dir_path) if f.endswith(('.yaml'))]
            #返回所有文件名
            return sorted(files)
        else:
            try:
                path = os.path.join(self.base_dir, 'sql_scripts', filename)
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                # 返回 yaml文件内容
                return data['changes']
            except FileNotFoundError:
                raise FileNotFoundError(f"未找到文件: {filename}")
    def _connect(self):
        """建立数据库连接"""
        try:
            self.conn = pymysql.connect(
                host=self.db_config['database']['host'],
                port=int(self.db_config['database']['port']),
                user=self.db_config['database']['user'],
                password=self.db_config['database']['password'],
                database=self.db_config['database']['dbname'],
                cursorclass=pymysql.cursors.DictCursor
            )
            self._init_table()
        except Error as e:
            raise RuntimeError(f"数据库连接失败: {e}")

    def _init_table(self):
        '''初始化创建表，表如果存在则不创建'''

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS `DATABASECHANGELOG` (
  `ID` bigint NOT NULL AUTO_INCREMENT,
  `CHANGEID` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `AUTHOR` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `COMMENT` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `FILENAME` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `DATEEXECUTED` datetime NOT NULL,
   PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 ROW_FORMAT=DYNAMIC;
        """
        with self.conn.cursor() as cursor:
            # 执行初始化 SQL
            cursor.execute(create_sql)
            self.conn.commit()


    def _get_applied_changeids(self) -> Set[str]:
        """获取已执行的sqlchangeid集合"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"SELECT CHANGEID FROM DATABASECHANGELOG"
            )
            return {row['CHANGEID'] for row in cursor.fetchall()}

    def _execute_script(self, id: str, author: str ,comment: str,filename: str,sql :str):
        """执行单个SQL脚本"""
        with self.conn.cursor() as cursor:
            try:
                print(f"正在执行版本 {filename} 的脚本")
                # 执行脚本中的所有SQL语句
                cursor.execute(sql)

                # 记录变更
                cursor.execute(
                    f"INSERT INTO DATABASECHANGELOG (CHANGEID, AUTHOR,COMMENT,FILENAME,DATEEXECUTED) VALUES ('{id}','{author}','{comment}','{filename}',now())"
                )
                self.conn.commit()
            except Error as e:
                self.conn.rollback()
                raise RuntimeError(f"执行脚本 {filename}--------------{id} 失败: {e}")

    def run_migrations(self):
        """执行所有未应用的迁移"""
        try:
            self._connect()
            applied_changeids = self._get_applied_changeids()
            executed_any = False  # ✅ 初始化变量

            #过滤配置文件中的指定版本
            if self.versions is None or self.versions.strip() in ('', 'None', '[]', '{}'):
                filename_list = self._load_yaml_changes()
                for filename in filename_list:
                    result = self._load_yaml_changes(filename)
                    for change in result:
                        if change['id'] not in applied_changeids:
                            self._execute_script(change['id'], change['author'], change['comment'], filename, change['sql'])
                            executed_any = True
                        else:
                            continue

            elif self.versions is not None:

                #将字符串转换为列表
                filename2_list = ast.literal_eval(self.versions)
                for filename2 in filename2_list:

                    result = self._load_yaml_changes(filename2)
                    for change in result:
                        if change['id'] not in applied_changeids:
                            self._execute_script(change['id'], change['author'], change['comment'], filename2,change['sql'])
                            executed_any = True
                        else:
                            continue
            if not executed_any:
                print("提示：没有新的迁移脚本需要执行。")
        except Exception as e:
            print(f"迁移失败: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()
        print("✅ 数据库迁移执行完毕。")

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.run_migrations()