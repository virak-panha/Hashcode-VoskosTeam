import os
import sys
from collections import defaultdict

from tqdm import tqdm


def video_endpoint_cost(_video, endpoint):
    if endpoint[1]:
        for (_cache, latency) in endpoint[1].items():
            if _video in CACHES[_cache]:
                return latency
        else:
            return endpoint[0]
    else:
        return 0


def request_cost(r):
    return video_endpoint_cost(r[0], ENDPOINTS[r[1]]) * r[2]


def how_much_can_we_improve(_video):
    _video_index = _video[0]
    _video_size = VIDEOS[_video_index]

    if BEST_CACHE_CACHE[_video_index] is not None:
        best_cache = BEST_CACHE_CACHE[_video_index]
        if _video_size <= CACHE_CAPACITY[best_cache[0]]:
            return best_cache[1], best_cache[0], _video

    requests = _video[1][1]

    saved_time = defaultdict(lambda: 0)
    for r in requests:
        caches = ENDPOINTS[r[1]][1]
        latency = ENDPOINTS[r[1]][0]
        current_cost = min([c[1] for c in caches.items() if _video[0] in CACHES[c[0]]] + [latency])

        for _cache in caches.items():
            space_left = CACHE_CAPACITY[_cache[0]]

            if _video_size < space_left:
                if current_cost - _cache[1] > 0:
                    saved_time[_cache[0]] += (current_cost - _cache[1]) * r[2]

    if not saved_time:
        del vids[_video[0]]
        pbar.update(1)
        return 0, None, _video

    best_cache = sorted(saved_time.items(), key=lambda x: x[1], reverse=True)[0]

    BEST_CACHE_CACHE[_video_index] = best_cache
    # (time saved, cache, video)
    return best_cache[1], best_cache[0], _video


if __name__ == '__main__':
    InputFolder = ''
    OutputFolder = ''

    if len(sys.argv) < 3:
        InputFolder = '..\inputVideos'  # Reads all the files inside this folder
        OutputFolder = 'output'  # Same names as input
    else:
        InputFolder = sys.argv[1]
        OutputFolder = sys.argv[2]

    if not os.path.exists(InputFolder):
        print('The given input folder argument is invalid..')
        sys.exit(-1)

    for video_file_name in os.listdir(InputFolder):
        video_path = os.path.join(InputFolder, video_file_name)
        print('Processing: ' + video_file_name)
        with open(video_path, 'r') as file:
            line = file.readline()
            [Videos, Endpoints, Requests, Caches, CacheSize] = [int(n) for n in line.split()]  # Cardinalities
            line = file.readline()
            VIDEOS = [int(n) for n in line.split()]
            ENDPOINTS = []
            REQUESTS = []
            CACHES = defaultdict(lambda: set())
            CACHE_CAPACITY = defaultdict(lambda: CacheSize)
            BEST_CACHE_CACHE = defaultdict(lambda: None)

            for _ in range(Endpoints):  # Read info for each Endpoint
                line = file.readline()
                [datacenterLatency, numOfConCaches] = [int(n) for n in line.split()]
                curEndpoint = (datacenterLatency, dict())  # curEndpoint[0] = datacenterLatency

                for _ in range(numOfConCaches):  # Read info for each cache and its latency
                    line = file.readline()
                    [cur_cache, cur_cache_latency] = [int(n) for n in line.split()]
                    # Save on each Endpoint every available cache and its latency
                    curEndpoint[1][cur_cache] = cur_cache_latency

                ENDPOINTS.append(curEndpoint)  # Save every Endpoint in random order (read order)

            for _ in range(Requests):  # For each request save tuple (video endpoint requests)
                line = file.readline()
                REQUESTS.append(tuple([int(n) for n in line.split()]))

            # lambda sets the default value for every new item inserted in the dict. Avoids for-loop for init.
            vids = defaultdict(lambda: [0, []])
            for req in tqdm(REQUESTS, desc='Requests'):  # tuples: (video endpoint requests)
                vids[req[0]][0] += request_cost(req)  # vids[video][0] += cost
                vids[req[0]][1].append(req)  # vids[video][1].append(req)

            pbar = tqdm(total=len(vids))
            pbar.set_description('Videos')
            while vids:
                # A list of the results of applying the function to the items of the argument sequence
                vid_list = map(how_much_can_we_improve, list(vids.items()))  # (time saved, cache, video)
                # Max finds
                time_saved, cache, video = max(vid_list, key=lambda x: VIDEOS[x[2][0]])
                if cache is None:
                    continue

                video_index = video[0]
                video_size = VIDEOS[video_index]

                CACHES[cache].add(video_index)
                CACHE_CAPACITY[cache] -= video_size
                BEST_CACHE_CACHE[video_index] = None
                video[1][0] -= time_saved
            pbar.close()

            output_path = os.path.join(OutputFolder, video_file_name.replace('.in', '.out'))
            if not os.path.exists(OutputFolder):
                os.makedirs(OutputFolder)

            with open(output_path, 'w') as out_file:
                out_file.write('{}\n'.format(CACHES.items().__len__()))
                for cache, videos in CACHES.items():
                    if videos:
                        out_file.write('{0} {1}\n'.format(cache, " ".join(map(str, list(videos)))))

            print('Done processing ' + video_file_name + '\n\n')
