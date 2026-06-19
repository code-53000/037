<template>
  <div class="not-found">
    <div class="error-code">404</div>
    <h1>页面不存在</h1>
    <p>你访问的页面可能已被删除或不存在</p>
    <el-button type="primary" size="large" @click="$router.push('/')">返回首页</el-button>
  </div>
</template>

<script setup></script>

<style lang="scss" scoped>
.not-found {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;

  .error-code {
    font-size: 120px;
    font-weight: 900;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    line-height: 1;
    margin-bottom: 16px;
  }

  h1 {
    font-size: 28px;
    margin: 0 0 10px;
  }

  p {
    color: #909399;
    margin: 0 0 24px;
  }
}
</style>
