import argparse
import re
import json
import os
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)


# 读取命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description="日志分析工具")
    parser.add_argument("log_file", help="日志文件的路径")  # 只传入日志文件路径
    return parser.parse_args()


# 解析日志文件
def parse_log(log_file, fault_dict):
    with open(log_file, "r", encoding="utf-8") as f:
        logs = f.readlines()

    is_cutting = False
    all_error_entries = []  # (line, code, desc)
    matched_error_entries = []  # (line, code, desc)

    code_pattern = re.compile(r"primary error\s*\[(0x)?([0-9A-Fa-f]+)\]")

    for i, line in enumerate(logs):
        line = line.strip()

        if "KEY_START_OK" in line:
            if is_cutting:
                print("检测到割草任务完成或停机，开始新一轮割草任务。")
            print(
                "\n*************************************************************************************************************\n"
            )
            print(f"{line}  # 割草机开始切割")
            is_cutting = True

        elif "MANUAL_WORK_SUCCESS" in line and is_cutting:
            print(f"{line}  # 割草完成")

        elif "EXCEPTION_EXIT_MOW_SUCCESS" in line and is_cutting:
            print(f"{line}  # 手动拍停")
            is_cutting = False

        elif "MANUAL_WORK_FAIL" in line and is_cutting:
            print(f"{line}  # 异常停机")
            print("检测到异常停机，查找后续的故障码信息：")
            for j in range(i + 1, len(logs)):
                match = code_pattern.search(logs[j])
                if match:
                    code = match.group(2).upper().lstrip("0") or "0"
                    desc = fault_dict.get(code, "未知故障")
                    matched_error_entries.append((logs[j].strip(), code, desc))
                    print(Fore.RED + f"{logs[j].strip()}  -> {desc}" + Style.RESET_ALL)
                if "KEY_START_OK" in logs[j]:
                    break

        # 收集所有故障码（无论是不是异常停机）
        match = code_pattern.search(line)
        if match:
            code = match.group(2).upper().lstrip("0") or "0"
            desc = fault_dict.get(code, "未知故障")
            all_error_entries.append((line, code, desc))

    # === 统计结果 ===
    print("\n" + "=" * 30 + " 统计结果 " + "=" * 30)

    # 总故障码（白色）
    print(Style.BRIGHT + f"\n总故障码数量: {len(all_error_entries)}" + Style.RESET_ALL)
    for line, code, desc in all_error_entries:
        print(f"    {line} -> {desc}")

    # 已匹配（红色）
    print(
        Style.BRIGHT
        + Fore.RED
        + f"\n已匹配故障码数量: {len(matched_error_entries)}"
        + Style.RESET_ALL
    )
    for line, code, desc in matched_error_entries:
        print(Fore.RED + f"    {line} -> {desc}" + Style.RESET_ALL)

    # 未匹配（黄色）
    unmatched_error_entries = [
        entry for entry in all_error_entries if entry not in matched_error_entries
    ]
    print(
        Style.BRIGHT
        + Fore.YELLOW
        + f"\n未匹配故障码数量: {len(unmatched_error_entries)}"
        + Style.RESET_ALL
    )
    for line, code, desc in unmatched_error_entries:
        print(Fore.YELLOW + f"    {line} -> {desc}" + Style.RESET_ALL)

    print("\n日志解析完成.")


def main():
    args = parse_args()

    # 固定 JSON 文件名
    json_file = "fault_code.json"

    if not os.path.exists(json_file):
        print(f"JSON文件不存在: {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        fault_dict = json.load(f)

    # 规范化 key
    normalized_fault_dict = {}
    for k, v in fault_dict.items():
        key = str(k).upper().lstrip("0") or "0"
        normalized_fault_dict[key] = v

    parse_log(args.log_file, normalized_fault_dict)


if __name__ == "__main__":
    main()
