@echo off
chcp 65001 > nul
echo 运行测试并生成Allure报告...
python run_tests.py %*

if %ERRORLEVEL% NEQ 0 (
    echo 测试运行过程中出现错误，错误代码: %ERRORLEVEL%
) else (
    echo 测试完成，没有错误。
)

echo.
echo 测试结果保存在: allure-results\latest
echo 测试报告保存在: allure-report\latest
echo 您可以通过浏览器打开 allure-report\latest\index.html 查看报告
pause 