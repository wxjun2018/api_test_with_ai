import pytest

class TestSimple:
    """简单测试用例类"""
    
    def test_simple_pass(self):
        """测试简单通过用例"""
        assert True
    
    @pytest.mark.xfail(reason="这是一个预期的失败，用于演示测试框架功能")
    def test_simple_fail(self):
        """测试简单失败用例"""
        assert False, "这是一个预期的失败"
    
    def test_with_description(self):
        """这是一个带有详细描述的测试用例
        
        测试步骤:
        1. 执行第一步操作
        2. 执行第二步操作
        3. 验证结果
        
        预期结果:
        - 所有步骤都成功执行
        """
        result = 1 + 1
        assert result == 2, f"预期结果为2，实际结果为{result}"
    
    @pytest.mark.slow
    def test_marked_test(self):
        """带有标记的测试用例"""
        assert True 