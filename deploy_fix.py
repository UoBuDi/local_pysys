import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('172.32.48.238', username='root', password='JZbACG9dDFJGFwsz')

stdin, stdout, stderr = ssh.exec_command("curl -s -X GET 'http://127.0.0.1:8001/api/users/?pageIndex=1&pageSize=10' -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc4MDM2OTk2NiwidHlwZSI6ImFjY2VzcyJ9.LLQUFUuLeN11dTchmiRTfWQY4fduWrSlZwtp4-J9v-Q'")
result = stdout.read().decode()
print('接口返回:', result[:500])

ssh.close()
