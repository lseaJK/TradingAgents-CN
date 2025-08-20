# 飞书自建应用权限梳理

## 1. 创建表格
- 需要权限：
  - 创建表格内容（如 Table Block、Sheet Block、Bitable）时，需有“编辑文档”或“编辑表格”权限。
  - 若涉及多维表格（Bitable），需有“管理多维表格”权限。
  - 相关 API 通常要求 tenant_access_token 或 user_access_token。

## 2. 创建文档
- 需要权限：
  - “创建文档”权限（如 POST /open-apis/docx/v1/documents）。
  - 需有“管理云空间文件”权限。
  - 相关 API 通常要求 tenant_access_token 或 user_access_token。

## 3. 修改表格
- 需要权限：
  - “编辑表格”权限（如插入/删除行列、合并/拆分单元格、调整列宽等）。
  - “管理表格”权限（如更新表格属性、样式等）。
  - 相关 API 通常要求 tenant_access_token 或 user_access_token。

## 4. 修改文档
- 需要权限：
  - “编辑文档”权限（如更新标题、插入内容块、删除内容块、替换文本等）。
  - 相关 API 通常要求 tenant_access_token 或 user_access_token。

## 5. 更新表格
- 需要权限：
  - “编辑表格”或“管理表格”权限（如更新列属性、合并/拆分单元格、批量更新内容等）。
  - 相关 API 通常要求 tenant_access_token 或 user_access_token。

## 6. 更新文档
- 需要权限：
  - “编辑文档”权限（如更新标题、批量插入/删除内容块等）。
  - 相关 API 通常要求 tenant_access_token 或 user_access_token。


---

### 权限获取流程与Token机制
#### 1. 获取 tenant_access_token（应用级权限令牌）
- 适用场景：自建应用调用大部分API时使用。
- 获取流程：
  1. 使用 FEISHU_APP_ID 和 FEISHU_APP_SECRET 发送 POST 请求到：
     `https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/`
  2. 请求体：
     ```json
     {
       "app_id": "<app_id>",
       "app_secret": "<app_secret>"
     }
     ```
  3. 返回结果中包含 `tenant_access_token` 字段。
- 时效性：
  - 有效期通常为 2 小时（7200 秒），到期后需重新获取。
- 刷新方式：
  - 直接重复上述流程重新获取，无需单独刷新接口。

#### 2. 获取 user_access_token（用户授权令牌）
获取 user_access_token（OAuth）：
  1. 用户访问授权链接：
     ```
     https://open.feishu.cn/open-apis/authen/v1/index?app_id=<FEISHU_APP_ID>&redirect_uri=<REDIRECT_URI>&state=<STATE>
     ```
     用户同意授权后，浏览器会跳转到 `REDIRECT_URI`，并携带 `code` 参数。
  2. 后端使用 code 换取 user_access_token：
     ```shell
     curl -X POST 'https://open.feishu.cn/open-apis/authen/v1/access_token' \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d '{
       "app_id": "<FEISHU_APP_ID>",
       "app_secret": "<FEISHU_APP_SECRET>",
       "grant_type": "authorization_code",
       "code": "<code>",
       "redirect_uri": "<REDIRECT_URI>"
     }'
     ```
     返回结果中包含 `user_access_token`、`refresh_token` 等字段。
  3. user_access_token 有效期一般为2小时，到期后用 refresh_token 刷新。

刷新 user_access_token：
  - 使用 refresh_token 调用刷新接口：
    ```shell
    curl -X POST 'https://open.feishu.cn/open-apis/authen/v1/refresh_access_token' \
    -H 'Content-Type: application/json; charset=utf-8' \
    -d '{
      "app_id": "<FEISHU_APP_ID>",
      "app_secret": "<FEISHU_APP_SECRET>",
      "grant_type": "refresh_token",
      "refresh_token": "<refresh_token>"
    }'
    ```

---

### 参考
- [飞书开放平台 API 权限说明](https://open.feishu.cn/document/ukTMukTMukTM/uAzM5YjLwMTO24CMzkjN)
- [Sheets API 权限要求](https://open.feishu.cn/document/ukTMukTMukTM/ucDO3EjL3gTNx4yN)
- [Docx API 权限要求](https://open.feishu.cn/document/ukTMukTMukTM/uAzM5YjLwMTO24CMzkjN)
  - 查看、评论、编辑、管理所有云空间文件
- Docx API（文档相关）：
  - 编辑文档、管理文档、管理云空间文件
- Bitable API（多维表格）：
  - 管理多维表格、编辑多维表格

---

### 参考
- [飞书开放平台 API 权限说明](https://open.feishu.cn/document/ukTMukTMukTM/uAzM5YjLwMTO24CMzkjN)
- [Sheets API 权限要求](https://open.feishu.cn/document/ukTMukTMukTM/ucDO3EjL3gTNx4yN)
- [Docx API 权限要求](https://open.feishu.cn/document/ukTMukTMukTM/uAzM5YjLwMTO24CMzkjN)


