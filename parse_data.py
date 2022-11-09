import pandas as pd


def parse_summary(file):
    summary = pd.read_csv(file)
    return {
        'CR': summary['CR'].tolist()[0],
        'Planting': summary['PDAT'].tolist()[0],
        'Germinate': summary['EDAT'].tolist()[0],
        'Harvest': summary['HDAT'].tolist()[0],
        'Yield': summary['HWAH'].tolist()[0]    # kg/ha
    }


def parse_plantgro(file):
    plantgro = pd.read_csv(file)
    return {
        'LAID': plantgro['LAID'],
        'Water Stress': plantgro['EWSD'],
        'Nitrogen Stress': plantgro['NSTD'],
        'Root Depth': plantgro['RDPD'],
        'Canopy Height': plantgro['CHTD']
    }


def parse_mgmtevent(mgmtevent):
    with open(mgmtevent, 'r') as me:
        keys = ['RUN',
                'Date',
                'DOY',
                'DAS',
                'DAP',
                'CR',
                'Stage',
                'Operation',
                'Quantities']
        events = []
        for i, line in enumerate(me):
            if i >= 6:
                event = [x.strip('.').strip() for x in line.split('  ') if x.strip()]
                if len(event) == 0:
                    break
                # Formatting
                run_no = event[0][0]
                event[0] = event[0][1:]
                if len(event[0]) <= 4:
                    month = ''.join([x for x in event.pop(0) if not x.isdigit()])
                    event[0] = month + ' ' + event[0]
                event = [run_no] + event
                event = [x.strip() for x in event]

                # Make to key-val
                if len(event) < len(keys):
                    event.insert(6, 'NaN')
                    if len(event) < len(keys):
                        event.insert(8, 'NaN')
                event = {key: val for key, val in zip(keys, event)}
                events.append(event)

        temp_solution = []
        temp_stage = []

        for event in events:
            if not event['Operation'][0].isdigit():
                temp_solution.append(
                    {
                        'Operation': event['Operation'],
                        'Quantities': event['Quantities'],
                        'DOY': event['DOY']
                    }
                )
            else:
                temp_stage.append(
                    {
                        'Stage': event['Operation'][3:],
                        'DOY': event['DOY']
                    }
                )

    return {'Stage': temp_stage,
            'Solution': temp_solution}


print(parse_summary('maize/summary.csv'))
for line in parse_mgmtevent('maize/MgmtEvent.OUT')['Solution']:
    print(line)

print(parse_plantgro('maize/plantgro.csv'))
