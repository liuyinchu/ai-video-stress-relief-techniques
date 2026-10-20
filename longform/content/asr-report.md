# 长片独立 ASR 与字幕对齐报告

全离线；没有台本提示词；原速原文件。差异是复听线索，不等于确认读错。
正式字幕边界来自匹配到的原始 ASR 词区间及邻近静音，未按字数切分词内时间。
识别 probability 门槛只是人工复核规则，不是经过校准的置信度。

当前章节：9/9；缺失：无

| 章 | 精确字符一致率 | 差异数 | 字幕复核数 | 阻断问题 |
| --- | ---: | ---: | ---: | --- |
| hook | 98.8% | 1 | 3 | 无 |
| breath | 95.2% | 8 | 12 | 无 |
| cold | 98.3% | 3 | 6 | 无 |
| ear | 97.2% | 4 | 4 | 无 |
| shake | 98.9% | 2 | 4 | 无 |
| paper | 93.5% | 6 | 8 | 无 |
| fractal | 99.0% | 2 | 3 | 无 |
| order | 99.5% | 1 | 2 | 无 |
| closing | 100.0% | 0 | 1 | 无 |

## hook

台本：压力一来，身体常常比念头先动起来：心跳加快，呼吸变浅，肩膀抬高。这是“战或逃”反应，明明坐在桌前，却像在等待一场冲刺。

要缓下来，可以从呼吸、触觉和眼前的小动作入手，给身体留一点余地，再去处理压力的来源。

原始识别：压力一来,身体常常比念头先动起来心跳加快,呼吸变浅,肩膀抬高这是站或逃反应明明坐在桌前,却像在等待一场冲刺要缓下来,可以从呼吸、触觉和眼前的小动作入手给身体留一点余地,再去处理压力的来源

- replace: 战 → 站
- hook-c002 [3.17–5.27s 原章音频] 心跳加快，呼吸变浅，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- hook-c004 [6.47–7.93s 原章音频] 这是“战或逃”反应，：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- hook-c005 [8.10–9.33s 原章音频] 明明坐在桌前，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.

## breath

台本：第一种，是双吸长呼，也叫生理性叹气。先坐稳，让肩膀自然放下。用鼻子吸一口气，吸到舒服的位置，再短短地补一小口。

接着，用嘴慢慢呼出，像轻轻叹一口气。让呼气比吸气从容一些，不必挤空肺，也不用追求声音或力度。

做完先恢复自然呼吸。可以试三到五轮，或更少，舒服最重要；头晕或不舒服就停，不必勉强。

叹气本来就有生理作用。肺里密布着细小的肺泡，较深的吸气有助于重新撑开部分闭合的肺泡，让气体交换继续顺畅进行。

把呼气拉长，也是在主动调整呼吸节奏。不过，二氧化碳并非排得越多越好；连续用力快喘，反而可能让人头晕。

二零二三年，包含休伯曼在内的团队发现，每天练习五分钟、持续一个月，双吸长呼有助改善情绪、降低呼吸频率。效果也因人而异。

原始识别：第一种是双吸长呼,也叫生理性叹气先坐稳,让肩膀自然放下用鼻子吸一口气,吸到舒服的位置再短短的补一小口接着,用嘴慢慢呼出,想轻轻叹一口气让呼气比吸气从容一些不避挤空肺,也不用追求声音或力度做完先恢复自然呼吸,可以是三到五轮或更少舒服最重要头晕或不舒服就停不必勉强碳气本来就有生理作用肺里密布着细小的肺泡较深的吸气有助于重新撑开部分闭合的肺泡让气体交换继续顺畅进行把呼气拉长也是在主动调整呼吸节奏不过二氧化碳并非排得越多越好连续用力快喘反而可能让人头晕2023年包含修博曼在内的团队发现每天练习五分钟持续一个月双膝肠呼有助改善情绪降低呼吸频率效果也因人而异

- replace: 地 → 的
- replace: 像 → 想
- replace: 必 → 避
- replace: 试 → 是
- replace: 叹 → 碳
- replace: 二零二三 → 2023
- replace: 休伯 → 修博
- replace: 吸长 → 膝肠
- breath-c001 [0.17–2.23s 原章音频] 第一种，是双吸长呼，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- breath-c003 [4.07–6.63s 原章音频] 先坐稳，让肩膀自然放下。：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- breath-c006 [10.10–11.57s 原章音频] 再短短地补一小口。：ASR differs from script; read the independent evidence and listen.
- breath-c008 [14.23–15.77s 原章音频] 像轻轻叹一口气。：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.；Non-exact lexical boundary anchor; review onset/end.
- breath-c010 [18.93–22.13s 原章音频] 不必挤空肺，也不用追求声音或力度。：ASR differs from script; read the independent evidence and listen.
- breath-c012 [24.50–25.97s 原章音频] 可以试三到五轮，：ASR differs from script; read the independent evidence and listen.
- breath-c014 [28.57–30.27s 原章音频] 头晕或不舒服就停，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- breath-c016 [31.70–33.67s 原章音频] 叹气本来就有生理作用。：ASR differs from script; read the independent evidence and listen.；Non-exact lexical boundary anchor; review onset/end.
- breath-c017 [33.87–36.10s 原章音频] 肺里密布着细小的肺泡，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- breath-c024 [53.63–56.80s 原章音频] 二零二三年，包含休伯曼在内的团队发现，：ASR differs from script; read the independent evidence and listen.；Non-exact lexical boundary anchor; review onset/end.
- breath-c025 [56.87–59.53s 原章音频] 每天练习五分钟、持续一个月，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- breath-c026 [59.63–63.57s 原章音频] 双吸长呼有助改善情绪、降低呼吸频率。：ASR differs from script; read the independent evidence and listen.

## cold

台本：第二种，借一点凉意。拿一条温度舒服的凉毛巾，轻轻贴在脸颊上，鼻口露出来，照常呼吸。把注意力放在清凉的触感上。

这个想法背后，有一个真实的生理现象，叫潜水反射。实验中，面部冷刺激配合屏息，可能使心率减慢，帮助身体节省氧气。

面部感觉主要经三叉神经传入脑干，心脏的迷走神经活动参与减慢心率。同时，外周血管也可能收缩，维持重要器官的供血。

心率慢下来，并不等于全身都放松。凉毛巾是温和的感官体验，也不保证复制实验里的潜水反射。

有心脏病、心率偏慢，或正在用减慢心率药物的人，不要自行尝试冰水浸脸和屏息。日常缓解压力，不必追求这种强烈刺激。

原始识别：第二种,接一点凉意,拿一条温度舒服的凉毛巾轻轻贴在脸颊上,鼻口露出来,照常呼吸,把注意力放在清凉的触感上。这个想法背后有一个真实的生理现象,叫潜水反射。实验中,面部冷刺激配合饼吸,可能使心率减慢,帮助身体节省氧气。面部感觉主要经三叉神经传入脑干,心脏的迷走神经活动参与减慢心率。同时,外周血管也可能收缩维持重要器官的供血心率慢下来并不等于全身都放松凉毛巾是温和的感官体验也不保证复制实验里的潜水反射有心脏病,心率偏慢或正在用减慢心率药物的人不要自行尝试冰水、净脸和屏息日常缓解压力不必追求这种强烈刺激

- replace: 借 → 接
- replace: 屏息 → 饼吸
- replace: 浸 → 净
- cold-c001 [0.13–2.07s 原章音频] 第二种，借一点凉意。：ASR differs from script; read the independent evidence and listen.
- cold-c004 [6.07–8.23s 原章音频] 鼻口露出来，照常呼吸。：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- cold-c009 [15.57–18.43s 原章音频] 实验中，面部冷刺激配合屏息，：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.；Non-exact lexical boundary anchor; review onset/end.
- cold-c010 [18.47–19.73s 原章音频] 可能使心率减慢，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- cold-c015 [30.93–32.57s 原章音频] 维持重要器官的供血。：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- cold-c021 [45.97–49.13s 原章音频] 不要自行尝试冰水浸脸和屏息。：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.

## ear

台本：第三种，把动作再缩小一点。用干净的指腹，轻轻揉一揉耳垂和耳廓边缘。慢慢移动，试上半分钟到一分钟，以舒服为准。

耳朵确实有丰富的感觉神经，其中某些区域有迷走神经的耳支。不过，耳垂和耳廓由多种神经共同支配，并不是一整圈放松按钮。

耳部电刺激研究，不能直接等同于用手按摩。把它当作触觉安抚，感受指腹、皮肤和温度；轻轻触碰，不用拉疼。

原始识别：第三种,把动作再缩小一点,用干净的指腹,轻轻揉一揉耳垂和耳阔边缘,慢慢移动,试上半分钟到一分钟,以舒服为准。耳朵确实有丰富的感觉神经,其中某些区域有迷走神经的耳汁。不过,耳垂和耳阔由多种神经共同支配,并不是一整圈放松按钮。耳部电刺激研究不能直接等同于用手按摩把它当作触觉安抚感受止腹皮肤和温度轻轻触碰不用拉疼

- replace: 廓 → 阔
- replace: 支 → 汁
- replace: 廓 → 阔
- replace: 指 → 止
- ear-c003 [4.03–7.17s 原章音频] 轻轻揉一揉耳垂和耳廓边缘。：ASR differs from script; read the independent evidence and listen.
- ear-c007 [14.83–17.67s 原章音频] 其中某些区域有迷走神经的耳支。：ASR differs from script; read the independent evidence and listen.；Non-exact lexical boundary anchor; review onset/end.
- ear-c008 [18.07–21.80s 原章音频] 不过，耳垂和耳廓由多种神经共同支配，：ASR differs from script; read the independent evidence and listen.
- ear-c013 [29.80–32.00s 原章音频] 感受指腹、皮肤和温度；：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.

## shake

台本：第四种，像小动物甩甩毛那样，松动身体。站稳，轻轻抖一抖手腕，再让手臂、膝盖和肩膀跟着动起来；坐着做也可以。

先从几十秒开始，舒服的话延长到一两分钟，保持自然呼吸，别甩头。随后停下来，感受肩膀和手脚有什么变化。

压力大时，我们容易握紧拳头、咬紧牙、把肌肉一直绷着。轻柔活动提供了一个改变姿势、重新留意身体感觉的机会。

这类动作常被称作躯体抖动。把它当作活动休息就好；目前没有可靠证据说明，抖动能排出压力激素，或直接甩掉创伤。

原始识别：第四种,像小动物甩甩毛那样,松动身体,站稳,轻轻抖一抖手腕,再让手臂、膝盖和肩膀跟着动起来,坐着坐,也可以。先从几十秒开始,舒服的话延长到一两分钟,保持自然呼吸,别甩头,随后停下来,感受肩膀和手脚有什么变化。压力大时,我们容易握紧拳头,摇紧牙,把肌肉一直绷着,轻柔活动提供了一个改变姿势,重新留意身体感觉的机会这类动作常被称作躯体抖动,把它当作活动休息就好目前没有可靠证据说明,抖动能排出压力激素或直接甩掉创伤

- replace: 做 → 坐
- replace: 咬 → 摇
- shake-c005 [10.13–11.57s 原章音频] 坐着做也可以。：ASR differs from script; read the independent evidence and listen.
- shake-c011 [23.37–28.40s 原章音频] 压力大时，我们容易握紧拳头、咬紧牙、把肌肉一直绷着。：ASR differs from script; read the independent evidence and listen.
- shake-c012 [28.47–33.80s 原章音频] 轻柔活动提供了一个改变姿势、重新留意身体感觉的机会。：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- shake-c015 [39.10–41.17s 原章音频] 目前没有可靠证据说明，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.

## paper

台本：第五种，让烦心事暂时落到纸上。找张废纸，写下此刻最让你恼火的几句话，不用修饰。然后揉成纸团，丢进纸篓。

如果只是想让手动起来，也可以慢慢撕一张废纸，听纸纤维断开的声音。动作有开头，也有结束，你能决定什么时候停下。

一项二零二四年的实验发现，受到挑衅后，写下想法再丢弃或碎纸的人，愤怒感比保留纸张的人下降得更多。研究针对的是愤怒。

可能起作用的，是把情绪写出来，再用丢弃给它画一个句号。研究并不说明，破坏得越用力就越解压。

原始识别：第五种让繁星室暂时落到纸上找张废纸写下此刻最让你恼火的几句话不用修饰然后揉成纸团丢进纸篓如果只是想让手动起来也可以慢慢撕一张废纸听纸纤维断开的声音动作有开头也有结束你能决定什么时候停下一向2024年的实验发现受到挑衅后写下想法再丢弃或碎纸的人愤怒感比保留纸张的人下降的更多研究针对的是愤怒可能起作用的是把情绪写出来再用丢气给他画一个句号研究并不说明破坏的越用力就越解压

- replace: 烦心事 → 繁星室
- replace: 项二零二四 → 向2024
- replace: 得 → 的
- replace: 弃 → 气
- replace: 它 → 他
- replace: 得 → 的
- paper-c001 [0.13–2.77s 原章音频] 第五种，让烦心事暂时落到纸上。：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c002 [3.03–6.53s 原章音频] 找张废纸，写下此刻最让你恼火的几句话，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c006 [10.60–12.43s 原章音频] 如果只是想让手动起来，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c011 [22.00–24.07s 原章音频] 一项二零二四年的实验发现，：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c013 [28.30–31.33s 原章音频] 愤怒感比保留纸张的人下降得更多。：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c015 [33.67–34.90s 原章音频] 可能起作用的，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c017 [36.60–38.73s 原章音频] 再用丢弃给它画一个句号。：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- paper-c019 [41.00–43.33s 原章音频] 破坏得越用力就越解压。：ASR differs from script; read the independent evidence and listen.

## fractal

台本：第六种，把目光借给自然。看看树叶的脉络、枝杈的分叉，或缓慢移动的云。给自己一两分钟，不用分析，也不用盯到眼睛发酸。

这些形状常带着分形的特征：放大一部分，还能看到相似的组织方式。枝干分成小枝，小枝再分叉，复杂之中又有熟悉的秩序。

研究者发现，观看某些自然景观和分形图案，可能帮助压力后的恢复。一种解释是，适度复杂而又有规律的图像，更容易让视觉系统处理。

这些研究的图案、样本和指标都不同，不能套用一个减压百分比。选舒服的画面，让注意力从追赶任务，转向安静地观看。

原始识别：第六种,把目光借给自然。看看树叶的脉络,枝叉的分叉或缓慢移动的云,给自己一两分钟,不用分析,也不用盯到眼睛发酸。这些形状常带着分形的特征,放大一部分还能看到相似的组织方式,枝干分成小枝,小枝再分叉,复杂之中又有熟悉的秩序。研究者发现,观看某些自然景观和分形图案,可能帮助压力后的恢复。一种解释是,适度、复杂而又有规律的图像更容易让视觉系统处理这些研究的图案、样本和指标都不同不能套用一个减压百分比选舒服的画面让注意力从追赶任务转向安静的观看

- replace: 杈 → 叉
- replace: 地 → 的
- fractal-c002 [2.83–5.30s 原章音频] 看看树叶的脉络、枝杈的分叉，：ASR differs from script; read the independent evidence and listen.
- fractal-c014 [35.87–39.07s 原章音频] 这些研究的图案、样本和指标都不同，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- fractal-c018 [44.63–46.17s 原章音频] 转向安静地观看。：ASR differs from script; read the independent evidence and listen.

## order

台本：第七种，整理一平米。先别把整个房间当任务，只选桌面的一小块：丢掉废纸，把杯子放好，让常用物品各归其位。

一平米是个提醒：把目标缩小到你现在做得完。每完成一个小动作，就有一个看得见的结果，注意力也有了具体的落点。

有研究发现，对家中杂乱的描述，与情绪和皮质醇的日间变化有关。但这只是相关，不能证明收拾桌面一定降低压力激素。

整理更实在的价值，是在一团乱里，找到一小块能着手改变的地方，可能带来一点安定感。做到这里就可以停，不必变成一场大扫除。

原始识别：第七种,整理一平米,先别把整个房间当任务,只选桌面的一小块,丢掉废纸,把杯子放好,让常用物品各归其位。一平米是个提醒,把目标缩小到你现在做得完,每完成一个小动作,就有一个看得见的结果,注意力也有了具体的落点。有研究发现对家中杂乱的描述与情绪和皮质唇的日间变化有关但这只是相关不能证明收拾桌面一定降低压力激素整理更实在的价值是在一团乱里找到一小块能着手改变的地方可能带来一点安定感做到这里就可以停不必变成一场大扫除

- replace: 醇 → 唇
- order-c011 [20.17–22.87s 原章音频] 有研究发现，对家中杂乱的描述，：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
- order-c012 [22.90–25.57s 原章音频] 与情绪和皮质醇的日间变化有关。：ASR differs from script; read the independent evidence and listen.；ASR word probability below review threshold 0.65; not a calibrated confidence interval.

## closing

台本：这七种方法，有的研究多一些，有的更接近个人的舒适体验。你可以挑一两种，留意自己的反应，慢慢找到适合自己的节奏。

先让身体松一点，再处理眼前的事。如果压力持续影响睡眠、工作或生活，也值得找专业人士一起面对。缓下来，是给自己重新选择的空间。

原始识别：这七种方法有的研究多一些有的更接近个人的舒适体验你可以挑一两种留意自己的反应慢慢找到适合自己的节奏先让身体松一点再处理眼前的事如果压力持续影响睡眠工作或生活也值得找专业人士一起面对缓下来是给自己重新选择的空间

- closing-c002 [2.73–4.97s 原章音频] 有的更接近个人的舒适体验。：ASR word probability below review threshold 0.65; not a calibrated confidence interval.
