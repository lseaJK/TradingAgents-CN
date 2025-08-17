## 项目同步记录
日期：2025-08-16
操作：将本地 TradingAgents-CN-main 项目所有内容同步并推送到远程仓库 git@github.com:lseaJK/TradingAgents-CN.git。
命令执行：
1. git add .
2. git commit -m "同步本地项目到远程仓库"
3. git push origin master
结果：推送成功，所有文件已同步到远程仓库 master 分支。

## powershell 环境激活
```powershell
cd E:\my_agent_learning\TradingAgents\TradingAgents-CN-main
env\Scripts\activate
```
## 飞书工具调用与 access_token 获取

### 获取 access_token
1. 推荐使用 refresh_feishu_token.py 脚本自动刷新 access_token。
2. 命令示例：
	```powershell
	cd E:\my_agent_learning\TradingAgents\TradingAgents-CN-main
	python .\refresh_feishu_token.py
	```
3. access_token 会自动写入配置文件或环境变量，供后续脚本和 API 调用。
4. 若 access_token 过期，需重新运行上述脚本。

### 调用飞书工具
1. 确保 access_token 有效后，可通过官方 SDK 或 REST API 进行表格、文档等操作。
2. 相关 API 参数（如表格ID、API密钥）建议统一配置在 .env 或 config 文件中。
3. 具体调用方法可参考 refresh_feishu_token.py 及项目相关脚本。


