## JSON Schema（模板定义）

```
{
  "report_date": "",
  "paper": {
    "title": "",
    "title_zh": "",
    "one_line_summary": "",
    "arxiv_id": "",
    "url": "",
    "published_date": "",
    "version": "",
    "field_tags": [],
    "code_url": "",
    "data_url": ""
  },
  "authors": {
    "first_author": {
      "name": "",
      "affiliation": "",
      "role": ""
    },
    "corresponding_advisor": {
      "name": "",
      "title": "",
      "research_focus": "",
      "homepage": ""
    },
    "research_group": {
      "name": "",
      "institution": "",
      "notable_works": [],
      "influence_signals": []
    }
  },
  "abstract_zh": "",
  "contributions": [],
  "key_results": [],
  "reading_advice": "",
  "automation_fields": {
    "freshness": {
      "type": "",
      "days_since_published": 0
    },
    "credibility_score": {
      "stars": 0,
      "breakdown": {
        "group_influence": 0,
        "open_source": 0,
        "experiment_completeness": 0
      },
      "rationale": ""
    }
  }
}
```

## YAML 版本（同一套字段，更易人工核对）

```
report_date: ""
paper:
  title: ""
  title_zh: ""
  one_line_summary: ""
  arxiv_id: ""
  url: ""
  published_date: ""
  version: ""
  field_tags: []
  code_url: ""
  data_url: ""
authors:
  first_author:
    name: ""
    affiliation: ""
    role: ""
  corresponding_advisor:
    name: ""
    title: ""
    research_focus: ""
    homepage: ""
  research_group:
    name: ""
    institution: ""
    notable_works: []
    influence_signals: []
abstract_zh: ""
contributions: []
key_results: []
reading_advice: ""
automation_fields:
  freshness:
    type: ""              # new_submission | new_version | old
    days_since_published: 0
  credibility_score:
    stars: 0              # 1-5
    breakdown:
      group_influence: 0          # 0-2
      open_source: 0              # 0-1.5
      experiment_completeness: 0  # 0-1.5
    rationale: ""
```

## 字段与评分规则说明

新鲜度（freshness.type）建议三档：new_submission 表示今日首次提交，new_version 表示旧论文新版本（v2/v3 等），old 表示历史论文补录。脚本可用 arXiv 元数据里的提交时间与 report_date 相减得到 days_since_published。

可信度评分（credibility_score）满分 5 星，由三项加权得到，方便脚本机械计算：课题组影响力 group_influence 占 0–2 分（依据被引量、知名项目、Fellow/获奖等信号）；是否开源 open_source 占 0–1.5 分（代码+数据全开 1.5，仅其一 0.75，未开源 0）；实验完备度 experiment_completeness 占 0–1.5 分（多基准+消融+对比 baseline 给满）。三项相加四舍五入到 0.5 星即为 stars。

## 填充示例（OmniVideo-100K）

```
{
  "report_date": "2026-06-21",
  "paper": {
    "title": "OmniVideo-100K: A Dataset for Audio-Visual Reasoning through Structured Scripts and Evidence Chains",
    "title_zh": "OmniVideo-100K：通过结构化脚本与证据链实现音视频推理的数据集",
    "one_line_summary": "提出实体锚定脚本+线索引导问答生成的自动化数据引擎，构建10万规模音视频推理指令数据集，显著提升全模态大模型的跨模态时序推理能力。",
    "arxiv_id": "2606.14702",
    "url": "https://arxiv.org/abs/2606.14702",
    "published_date": "2026-06-17",
    "version": "v2",
    "field_tags": ["多模态大模型", "音视频理解", "数据集", "指令微调"],
    "code_url": "https://github.com/MiG-NJU/OmniVideo-100K",
    "data_url": "https://huggingface.co/datasets/MiG-NJU/OmniVideo-100K"
  },
  "authors": {
    "first_author": {
      "name": "Xinyue Cai（蔡馨悦）",
      "affiliation": "南京大学",
      "role": "学生"
    },
    "corresponding_advisor": {
      "name": "傅朝友（Chaoyou Fu）",
      "title": "南京大学智能科学与技术学院研究员/助理教授/博导",
      "research_focus": "多模态大模型",
      "homepage": "https://bradyfu.github.io/"
    },
    "research_group": {
      "name": "南京大学米格小组（MiG-NJU）",
      "institution": "南京大学",
      "notable_works": ["VITA 全模态交互大模型", "Video-MME 视频理解评测基准", "Awesome-MLLM"],
      "influence_signals": [
        "Video-MME 为视频理解领域高被引权威基准",
        "傅朝友 Google Scholar 被引超 8000，入选中国科协青年人才托举工程，获中科院院长特别奖",
        "合作者赫然为 IAPR/IEEE Fellow、CASIA NLPR 全职教授"
      ]
    }
  },
  "abstract_zh": "针对音视频问答自动化构建中‘视频—字幕—问答’范式切断声画关联、跨段实体描述不一致、问题缺乏长时序与深度跨模态推理的问题，作者提出两阶段数据引擎：实体锚定脚本以主要实体列表为全局先验生成结构化脚本，重建声画关联并保证跨段一致性；线索引导问答生成先挖掘跨段跨模态线索再据此生成问答对。基于此构建10万规模的 OmniVideo-100K 与505条人工校验的 OmniVideo-Test。",
  "contributions": [
    "提出实体锚定视频脚本化方法，以主要实体列表为全局先验，解决跨片段指代不一致与声画关联断裂。",
    "提出线索引导的两步问答生成（全局线索挖掘+局部聚焦生成），使问题平均时序跨度达144.75s（直接生成仅76.24s）。",
    "构建并开源 OmniVideo-100K 数据集与人工校验测试集，覆盖对齐/理解/推理三层共十类任务。"
  ],
  "key_results": [
    "OmniVideo-Test 上 VITA-1.5、Qwen2.5-Omni-7B、Qwen3-Omni-30B 微调后分别提升 20.59%、17.82%、13.86%。",
    "Daily-Omni、JointAVBench 等基准泛化提升最高 12.64%，且不损害 Video-MME 通用视频理解能力。",
    "对比 AVQA、JavisInst-Und，仅本数据集在多数基准上带来一致正向增益。"
  ],
  "reading_advice": "强烈推荐做全模态/音视频大模型、多模态数据合成与指令微调的研究者精读方法第2节与消融实验；团队为 VITA/Video-MME 出品方，数据质量可信度高。",
  "automation_fields": {
    "freshness": {
      "type": "new_version",
      "days_since_published": 4
    },
    "credibility_score": {
      "stars": 5,
      "breakdown": {
        "group_influence": 2,
        "open_source": 1.5,
        "experiment_completeness": 1.5
      },
      "rationale": "课题组为 VITA/Video-MME 团队（影响力满分）；代码+数据集均开源（满分）；含多基准评测、消融与跨数据集对比（满分），合计 5.0 星。"
    }
  }
}
```

这套结构可以直接喂给脚本：从 arXiv API 拿到标题、ID、提交时间、版本、摘要；新鲜度和可信度三项分数可由规则函数自动算出；一作和导师/课题组影响力字段需要一次额外的 Scholar/主页检索来填充（这是唯一较难全自动的部分，可以缓存作者—课题组映射表来加速）。