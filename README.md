PyDut/
├── conf/
│   └── db.conf                # 作用：存储数据库连接信息（host、port、user、password、dbname）、存储需要执行的版本号列表（versions.version）
├── lib/
│   └── main.py                # 主程序逻辑，数据库迁移脚本执行器
├── sql_scripts/               # 存放 YAML 格式的 SQL 变更脚本
│   ├── *.yaml                 # 每个 YAML 文件代表一个版本的变更集
├── start.sh                   # 项目启动脚本（Shell）
