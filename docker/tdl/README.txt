本目录用于在「构建镜像时无法访问 GitHub」时，由你本机预先放入 tdl 的 Linux amd64 制品。

任选其一即可：

1) 官方压缩包（推荐）
   从发布页下载与 Dockerfile 期望一致的文件，放到本目录并命名为：
   tdl_Linux_64bit.tar.gz
   示例地址（版本号请自行替换）：
   https://github.com/iyear/tdl/releases/download/v0.20.2/tdl_Linux_64bit.tar.gz

2) 仅可执行文件
   将解压得到的 Linux amd64 二进制命名为 tdl（无后缀），放在本目录。

构建镜像前请确保上述文件之一存在；否则 docker build 会在安装 tdl 的步骤失败。
